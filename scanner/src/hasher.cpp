#include "hasher.h"
#include "xxhash.h"

#include <sys/stat.h>
#include <fstream>
#include <vector>
#include <string>
#include <unordered_map>
#include <cstdio>
#include <cstdint>
#include <utility>

namespace {

std::string to_hex(uint64_t v) {
    char buf[17];
    std::snprintf(buf, sizeof(buf), "%016llx",
                  static_cast<unsigned long long>(v));
    return std::string(buf);
}

// Partial hash: first 4KB of the file. Missing/unreadable files hash to the
// empty-input hash (callers should have already filtered by stat).
std::string partial_hash(const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    char buf[4096];
    f.read(buf, sizeof(buf));
    auto n = static_cast<size_t>(f.gcount());
    XXH64_hash_t h = XXH64(buf, n, 0);
    return to_hex(h);
}

// Full hash: stream the entire file in 64KB chunks.
std::string full_hash(const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    XXH64_state_t* st = XXH64_createState();
    XXH64_reset(st, 0);
    char buf[65536];
    while (f) {
        f.read(buf, sizeof(buf));
        auto n = static_cast<size_t>(f.gcount());
        if (n > 0) XXH64_update(st, buf, n);
    }
    XXH64_hash_t h = XXH64_digest(st);
    XXH64_freeState(st);
    return to_hex(h);
}

}  // namespace

std::vector<DupGroup> hash_files(const std::vector<std::string>& paths,
                                 int64_t min_size) {
    std::vector<DupGroup> result;

    struct FileInfo { std::string path; int64_t size; };
    std::vector<FileInfo> files;
    files.reserve(paths.size());
    for (const auto& p : paths) {
        struct stat st;
        if (stat(p.c_str(), &st) != 0) continue;
        if (!S_ISREG(st.st_mode)) continue;  // only regular files
        int64_t sz = static_cast<int64_t>(st.st_size);
        if (sz < min_size) continue;
        files.push_back({p, sz});
    }

    // 1. Group by size; only groups with 2+ files can hold duplicates.
    std::unordered_map<int64_t, std::vector<size_t>> by_size;
    for (size_t i = 0; i < files.size(); ++i) {
        by_size[files[i].size].push_back(i);
    }

    for (auto& size_group : by_size) {
        const std::vector<size_t>& idxs = size_group.second;
        if (idxs.size() < 2) continue;

        // 2. Group by partial hash (first 4KB).
        std::unordered_map<std::string, std::vector<size_t>> by_partial;
        for (size_t idx : idxs) {
            by_partial[partial_hash(files[idx].path)].push_back(idx);
        }

        for (auto& partial_group : by_partial) {
            const std::string& phash = partial_group.first;
            const std::vector<size_t>& pidxs = partial_group.second;
            if (pidxs.size() < 2) continue;

            // 3. Group by full hash.
            std::unordered_map<std::string, std::vector<size_t>> by_full;
            for (size_t idx : pidxs) {
                by_full[full_hash(files[idx].path)].push_back(idx);
            }

            for (auto& full_group : by_full) {
                const std::string& fhash = full_group.first;
                const std::vector<size_t>& fidxs = full_group.second;
                if (fidxs.size() < 2) continue;
                DupGroup g;
                g.size = files[fidxs[0]].size;
                g.hash_partial = phash;
                g.hash_full = fhash;
                g.paths.reserve(fidxs.size());
                for (size_t idx : fidxs) g.paths.push_back(files[idx].path);
                result.push_back(std::move(g));
            }
        }
    }

    return result;
}
