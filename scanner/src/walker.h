#pragma once
#include <string>
#include <vector>
#include <functional>
#include <cstdint>
#include "ndjson_writer.h"

void walk(const std::string& root,
          std::function<void(const std::string&)> callback,
          const std::vector<std::string>& excludes = {},
          bool follow_symlinks = false);

struct WalkResult {
    int64_t total_entries;
    int64_t total_bytes;
    int64_t cache_hits;
    int64_t cache_misses;
};

// Walk the tree under `root`, stat every entry with a thread pool, and emit
// NDJSON frames (entry / warn) via `writer`. If `cache_path` is non-empty the
// cache DB is opened (v1: no real lookups yet; all entries count as misses).
WalkResult walk_and_stat(const std::string& root, NdjsonWriter& writer,
                         const std::string& cache_path, int workers,
                         const std::vector<std::string>& excludes);
