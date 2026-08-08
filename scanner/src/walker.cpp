#include "walker.h"

#include <ftw.h>
#include <string>
#include <vector>
#include <functional>
#include <memory>
#include <atomic>
#include <csignal>

#include "ndjson_writer.h"
#include "stat_pool.h"
#include "cache.h"

#ifndef _WIN32
#include <fnmatch.h>
#endif

namespace {

// SIGINT graceful-cancel flag. Set by the signal handler installed in
// walk_and_stat; the stat callback checks it to stop emitting new frames.
std::atomic<bool> g_cancelled{false};
extern "C" void sigint_handler(int) { g_cancelled = true; }

// nftw does not accept user data portably; use thread_local globals.
thread_local std::function<void(const std::string&)>* g_callback = nullptr;
thread_local const std::vector<std::string>* g_excludes = nullptr;
thread_local WalkWarnFn* g_warn = nullptr;

#ifdef _WIN32
// MinGW lacks <fnmatch.h>; provide a portable glob matcher with
// semantics compatible with fnmatch() for the patterns we care about
// (*, ?, [..], [!..]). Sufficient for exclude basenames like "*.tmp".
static bool glob_match(const char* pattern, const char* str) {
    while (*pattern) {
        if (*pattern == '*') {
            while (*pattern == '*') ++pattern;
            if (!*pattern) return true;
            for (; *str; ++str) {
                if (glob_match(pattern, str)) return true;
            }
            return glob_match(pattern, str);
        } else if (*pattern == '?') {
            if (!*str) return false;
            ++pattern;
            ++str;
        } else if (*pattern == '[') {
            if (!*str) return false;
            ++pattern;
            bool negated = (*pattern == '!' || *pattern == '^');
            if (negated) ++pattern;
            bool matched = false;
            if (*pattern == ']') {
                if (*str == ']') matched = true;
                ++pattern;
            }
            while (*pattern && *pattern != ']') {
                if (pattern[0] && pattern[1] == '-' && pattern[2] && pattern[2] != ']') {
                    if (*str >= pattern[0] && *str <= pattern[2]) matched = true;
                    pattern += 3;
                } else {
                    if (*str == *pattern) matched = true;
                    ++pattern;
                }
            }
            if (*pattern == ']') ++pattern;
            if (negated) matched = !matched;
            if (!matched) return false;
            ++str;
        } else {
            if (*pattern != *str) return false;
            ++pattern;
            ++str;
        }
    }
    return *str == '\0';
}
#else
static bool glob_match(const char* pattern, const char* str) {
    return fnmatch(pattern, str, 0) == 0;
}
#endif

std::string basename_of(const char* fpath) {
    const char* base = fpath;
    for (const char* p = fpath; *p; ++p) {
        if (*p == '/' || *p == '\\') base = p + 1;
    }
    return base;
}

int nftw_cb(const char* fpath, const struct stat* /*sb*/,
            int typeflag, struct FTW* /*ftwbuf*/) {
    // Traversal errors: emit a warn frame if a warn callback is registered,
    // then skip the offending subtree/entry without aborting the walk.
    if (typeflag == FTW_DNR) {
        if (g_warn && *g_warn) {
            (*g_warn)(fpath, "EACCES", "directory not readable");
        }
        return FTW_SKIP_SUBTREE;
    }
    if (typeflag == FTW_NS) {
        if (g_warn && *g_warn) {
            (*g_warn)(fpath, "EIO", "stat failed");
        }
        return FTW_CONTINUE;
    }
    // Exclude by glob match against basename.
    if (g_excludes && !g_excludes->empty()) {
        std::string base = basename_of(fpath);
        for (const auto& pat : *g_excludes) {
            if (glob_match(pat.c_str(), base.c_str())) {
                return FTW_SKIP_SUBTREE;
            }
        }
    }
    if (g_callback && *g_callback) {
        (*g_callback)(fpath);
    }
    return FTW_CONTINUE;
}

}  // namespace

void walk(const std::string& root,
          std::function<void(const std::string&)> callback,
          const std::vector<std::string>& excludes,
          bool follow_symlinks,
          WalkWarnFn warn) {
    g_callback = &callback;
    g_excludes = &excludes;
    WalkWarnFn* warn_ptr = warn ? &warn : nullptr;
    g_warn = warn_ptr;
    int flags = FTW_ACTIONRETVAL;
    if (!follow_symlinks) flags |= FTW_PHYS;
    nftw(root.c_str(), nftw_cb, 32, flags);
    g_callback = nullptr;
    g_excludes = nullptr;
    g_warn = nullptr;
}

namespace {

std::string type_from_mode(int32_t mode) {
    if (S_ISDIR(mode)) return "dir";
    if (S_ISREG(mode)) return "file";
#ifndef _WIN32
    if (S_ISLNK(mode)) return "link";
#endif
    return "other";
}

// Extension = substring after the last '.' that comes after the last path
// separator. A leading dot (hidden file like ".bashrc") is not an extension.
std::string ext_from_path(const std::string& path) {
    size_t last_sep = std::string::npos;
    for (size_t i = 0; i < path.size(); ++i) {
        if (path[i] == '/' || path[i] == '\\') last_sep = i;
    }
    size_t last_dot = path.rfind('.');
    if (last_dot == std::string::npos) return "";
    if (last_sep != std::string::npos && last_dot <= last_sep) return "";
    if (last_sep != std::string::npos && last_dot == last_sep + 1) return "";
    if (last_sep == std::string::npos && last_dot == 0) return "";
    return path.substr(last_dot + 1);
}

}  // namespace

WalkResult walk_and_stat(const std::string& root, NdjsonWriter& writer,
                         const std::string& cache_path, int workers,
                         const std::vector<std::string>& excludes) {
    WalkResult result{0, 0, 0, 0};

    // Install a SIGINT handler so Ctrl+C requests a graceful cancel: the stat
    // callback stops emitting new frames instead of aborting mid-write.
    g_cancelled = false;
    std::signal(SIGINT, sigint_handler);

    // 1. Collect all paths by walking the tree. Traversal errors
    // (permission-denied dirs, stat failures) become warn frames.
    std::vector<std::string> paths;
    walk(root, [&](const std::string& p) { paths.push_back(p); }, excludes,
         false,
         [&](const std::string& path, const std::string& code, const std::string& msg) {
             writer.write_warn(path, code, msg);
         });

    // 2. Optionally open the cache DB. v1: no real lookups yet; best-effort.
    std::unique_ptr<Cache> cache;
    if (!cache_path.empty()) {
        try {
            cache = std::make_unique<Cache>(cache_path);
            cache->open();
        } catch (...) {
            cache.reset();
        }
    }

    // 3. Stat every path with the thread pool. The StatPool invokes the
    // callback on the calling thread, so no synchronization is needed here.
    StatPool pool(workers);
    pool.run(paths, [&](const std::string& path, const StatResult& r) {
        if (g_cancelled.load()) {
            return;  // graceful cancel: stop emitting new frames
        }
        ++result.total_entries;
        if (!r.ok) {
            writer.write_warn(path, r.err_code, "stat failed");
            return;
        }
        result.total_bytes += r.size;
        ++result.cache_misses;  // v1: real cache integration comes later
        Entry e{};
        e.path = path;
        e.size = r.size;
        e.type = type_from_mode(r.mode);
        e.ext = ext_from_path(path);
        e.mode = r.mode;
        e.mtime = r.mtime;
        e.inode = r.inode;
        e.uid = r.uid;
        e.gid = r.gid;
        e.nlink = r.nlink;
        e.cached = false;
        writer.write_entry(e);
    });

    // Restore default SIGINT handling.
    std::signal(SIGINT, SIG_DFL);

    // 4. Flush + close the cache if it was opened.
    if (cache) {
        cache->flush_batch();
        cache->close();
    }

    return result;
}
