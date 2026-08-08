#pragma once
#include <string>
#include <vector>
#include <cstdint>

struct DupGroup {
    int64_t size;
    std::string hash_partial;  // xxhash64 of first 4KB, hex
    std::string hash_full;     // xxhash64 of full file, hex
    std::vector<std::string> paths;
};

// Find duplicate files among `paths`. Files smaller than `min_size` are
// ignored. Dedup happens in three stages: by size, by partial hash (first
// 4KB), then by full hash. Only groups surviving all stages (2+ identical
// files) are returned.
std::vector<DupGroup> hash_files(const std::vector<std::string>& paths,
                                 int64_t min_size);
