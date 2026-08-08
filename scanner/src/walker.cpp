#include "walker.h"

#include <ftw.h>
#include <string>
#include <vector>
#include <functional>

#ifndef _WIN32
#include <fnmatch.h>
#endif

namespace {

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

// nftw does not accept user data portably; use thread_local globals.
thread_local std::function<void(const std::string&)>* g_callback = nullptr;
thread_local const std::vector<std::string>* g_excludes = nullptr;

std::string basename_of(const char* fpath) {
    const char* base = fpath;
    for (const char* p = fpath; *p; ++p) {
        if (*p == '/' || *p == '\\') base = p + 1;
    }
    return base;
}

int nftw_cb(const char* fpath, const struct stat* /*sb*/,
            int typeflag, struct FTW* /*ftwbuf*/) {
    // Permission/stat errors: skip silently for now (warn frames in Task 11).
    if (typeflag == FTW_DNR || typeflag == FTW_NS) {
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
          bool follow_symlinks) {
    g_callback = &callback;
    g_excludes = &excludes;
    int flags = FTW_ACTIONRETVAL;
    if (!follow_symlinks) flags |= FTW_PHYS;
    nftw(root.c_str(), nftw_cb, 32, flags);
    g_callback = nullptr;
    g_excludes = nullptr;
}
