#include <gtest/gtest.h>
#include <sstream>
#include <string>
#include "walker.h"
#include "ndjson_writer.h"
#include "test_util.h"

using testutil::TestDir;

TEST(Integration, WalkAndStatProducesEntries) {
    TestDir tmp("diskviz_integration");
    tmp.create_dir("sub");
    tmp.create_file("a.txt", "hello");
    tmp.create_file("sub/b.txt", "world!");

    std::ostringstream out;
    NdjsonWriter w(out);
    w.write_scan_start(tmp.path(), 1786097000, "test", 4);
    auto r = walk_and_stat(tmp.path(), w, "", 4, {});
    EXPECT_GE(r.total_entries, 3);
    EXPECT_GT(r.total_bytes, 0);
    std::string s = out.str();
    EXPECT_NE(s.find("\"type\":\"entry\""), std::string::npos);
    EXPECT_NE(s.find("\"kind\":\"dir\""), std::string::npos);
    EXPECT_NE(s.find("\"kind\":\"file\""), std::string::npos);
}
