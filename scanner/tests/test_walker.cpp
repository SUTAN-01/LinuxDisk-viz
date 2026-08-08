#include <gtest/gtest.h>
#include <vector>
#include <string>
#include "walker.h"
#include "test_util.h"

class WalkerTest : public ::testing::Test {
protected:
    std::string tmp;
    void SetUp() override {
        tmp = testutil::join(testutil::temp_dir(), "diskviz_walker_test");
        testutil::remove_tree(tmp);
        testutil::make_dir(tmp);
        testutil::make_dir(testutil::join(tmp, "sub1"));
        testutil::make_dir(testutil::join(tmp, "sub2"));
        testutil::make_dir(testutil::join(tmp, "sub2", "deep"));
        testutil::make_file(testutil::join(tmp, "a.txt"), "hello");
        testutil::make_file(testutil::join(tmp, "sub1", "b.txt"), "world");
        testutil::make_file(testutil::join(tmp, "sub2", "deep", "c.txt"), "!");
        testutil::make_file(testutil::join(tmp, "skip.tmp"), "tmp");
    }
    void TearDown() override { testutil::remove_tree(tmp); }
};

TEST_F(WalkerTest, WalksSimpleTree) {
    std::vector<std::string> paths;
    walk(tmp, [&](const std::string& p) { paths.push_back(p); });
    EXPECT_GE(paths.size(), 5u);
}

TEST_F(WalkerTest, ExcludesByGlobPattern) {
    std::vector<std::string> paths;
    walk(tmp, [&](const std::string& p) { paths.push_back(p); }, {"*.tmp"});
    for (const auto& p : paths) {
        EXPECT_EQ(p.find(".tmp"), std::string::npos);
    }
}
