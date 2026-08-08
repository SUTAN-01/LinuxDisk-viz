#include <gtest/gtest.h>
#include <atomic>
#include <vector>
#include <string>
#include "stat_pool.h"
#include "test_util.h"

TEST(StatPool, StatsAllFilesCorrectly) {
    std::string tmp = testutil::join(testutil::temp_dir(), "diskviz_stat_test");
    testutil::remove_tree(tmp);
    testutil::make_dir(tmp);
    testutil::make_file(testutil::join(tmp, "f1.txt"), "hello");
    testutil::make_file(testutil::join(tmp, "f2.txt"), "world!");
    std::vector<std::string> paths = {
        testutil::join(tmp, "f1.txt"),
        testutil::join(tmp, "f2.txt"),
    };
    std::atomic<int> count{0};
    std::atomic<int64_t> total{0};
    StatPool pool(4);
    pool.run(paths, [&](const std::string&, const StatResult& r) {
        if (r.ok) { count++; total += r.size; }
    });
    EXPECT_EQ(count.load(), 2);
    EXPECT_EQ(total.load(), 11);
    testutil::remove_tree(tmp);
}

TEST(StatPool, HandlesMissingFile) {
    StatPool pool(2);
    std::atomic<int> errs{0};
    pool.run({"/nonexistent/xyz123"}, [&](const std::string&, const StatResult& r) {
        if (!r.ok) errs++;
    });
    EXPECT_EQ(errs.load(), 1);
}
