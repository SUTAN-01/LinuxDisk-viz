#include <gtest/gtest.h>
#include <string>
#include "hasher.h"
#include "test_util.h"

using testutil::TestDir;

TEST(Hasher, PartialHashShortCircuits) {
    TestDir tmp("diskviz_hash_test");
    tmp.create_file("a.bin", std::string(100, 'A'));
    tmp.create_file("b.bin", std::string(100, 'B'));
    tmp.create_file("c.bin", std::string(100, 'A'));  // same as a
    auto groups = hash_files({
        testutil::join(tmp.path(), "a.bin"),
        testutil::join(tmp.path(), "b.bin"),
        testutil::join(tmp.path(), "c.bin")
    }, 0);
    ASSERT_EQ(groups.size(), 1u);
    EXPECT_EQ(groups[0].paths.size(), 2u);
}

TEST(Hasher, HandlesEmptyFile) {
    TestDir tmp("diskviz_hash_empty");
    tmp.create_file("e1", "");
    tmp.create_file("e2", "");
    auto groups = hash_files({
        testutil::join(tmp.path(), "e1"),
        testutil::join(tmp.path(), "e2")
    }, 0);
    EXPECT_EQ(groups.size(), 1u);
}
