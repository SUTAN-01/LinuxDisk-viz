#include <gtest/gtest.h>
#include <chrono>
#include <cstdlib>
#include <sstream>
#include "walker.h"
#include "ndjson_writer.h"

// Performance baseline: scanning 100k files should finish well under 3s with
// 8 workers. Skipped unless DISKVIZ_PERF_DIR points at a generated dataset
// (see scripts/gen_perf_dataset.sh). Perf validation is expected on Linux.
TEST(Perf, Scan100kFilesUnder3s) {
    const char* dir = std::getenv("DISKVIZ_PERF_DIR");
    if (!dir) GTEST_SKIP() << "Set DISKVIZ_PERF_DIR to run perf test";

    std::ostringstream out;
    NdjsonWriter w(out);
    auto start = std::chrono::steady_clock::now();
    auto r = walk_and_stat(dir, w, "", 8, {});
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - start).count();

    EXPECT_LT(ms, 3000) << "Scan took " << ms << "ms, expected < 3000ms";
    std::cerr << "Scanned " << r.total_entries << " entries in " << ms
              << "ms (" << r.total_bytes << " bytes)\n";
}
