#include <gtest/gtest.h>
#include <fstream>
#include <cstdio>
#include "cache.h"
#include "test_util.h"

TEST(Cache, InsertAndLookupHits) {
    std::string db = testutil::join(testutil::temp_dir(), "diskviz_cache_test.sqlite");
    std::remove(db.c_str());
    {
        Cache cache(db);
        cache.open();
        cache.upsert({1, 1234, 5678, "/var/log/syslog", 6120234, 1786096000, 33188, "file", "log", 0, 0, 1});
        auto hit = cache.lookup(1, 1234, 1786096000, 6120234);
        ASSERT_TRUE(hit.has_value());
        EXPECT_EQ(hit->path, "/var/log/syslog");
        EXPECT_EQ(hit->size, 6120234);
    }
    std::remove(db.c_str());
}

TEST(Cache, MissWhenMtimeChanges) {
    std::string db = testutil::join(testutil::temp_dir(), "diskviz_cache_test2.sqlite");
    std::remove(db.c_str());
    {
        Cache cache(db);
        cache.open();
        cache.upsert({1, 1234, 5678, "/x", 100, 1000, 33188, "file", "", 0, 0, 1});
        auto hit = cache.lookup(1, 1234, 2000, 100);
        EXPECT_FALSE(hit.has_value());
    }
    std::remove(db.c_str());
}

TEST(Cache, RecoversFromCorruptFile) {
    std::string db = testutil::join(testutil::temp_dir(), "diskviz_corrupt.sqlite");
    std::remove(db.c_str());
    {
        std::ofstream f(db);
        f << "not a sqlite file";
    }
    {
        Cache cache(db);
        EXPECT_NO_THROW(cache.open());
        EXPECT_FALSE(cache.lookup(1, 1, 1, 1).has_value());
    }
    std::remove(db.c_str());
}
