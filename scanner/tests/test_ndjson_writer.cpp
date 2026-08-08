#include <gtest/gtest.h>
#include <sstream>
#include <algorithm>
#include "ndjson_writer.h"

TEST(NdjsonWriter, EscapesQuotesAndNewlines) {
    std::ostringstream out;
    NdjsonWriter w(out);
    w.write_entry({
        .path = "a\"b\nc",
        .size = 1, .type = "file", .ext = "",
        .mode = 0, .mtime = 0, .inode = 0,
        .uid = 0, .gid = 0, .nlink = 0, .cached = false
    });
    std::string line = out.str();
    ASSERT_FALSE(line.empty());
    EXPECT_EQ(line.back(), '\n');
    EXPECT_NE(line.find("\\\""), std::string::npos);
    EXPECT_NE(line.find("\\n"), std::string::npos);
    EXPECT_EQ(std::count(line.begin(), line.end(), '\n'), 1);
}

TEST(NdjsonWriter, EntryFrameHasTypeEntryAndKindField) {
    std::ostringstream out;
    NdjsonWriter w(out);
    w.write_entry({
        .path = "/x/y.txt",
        .size = 42, .type = "file", .ext = "txt",
        .mode = 33188, .mtime = 1000, .inode = 7,
        .uid = 0, .gid = 0, .nlink = 1, .cached = false
    });
    std::string line = out.str();
    // Frame discriminator must be "entry"
    EXPECT_NE(line.find("\"type\":\"entry\""), std::string::npos);
    // Filesystem type must be under "kind", NOT a duplicate "type"
    EXPECT_NE(line.find("\"kind\":\"file\""), std::string::npos);
    // Ensure no second "type" key overwriting the frame discriminator
    size_t first = line.find("\"type\":\"");
    size_t second = line.find("\"type\":\"", first + 1);
    EXPECT_EQ(second, std::string::npos);
}

TEST(NdjsonWriter, WritesScanStartFrame) {
    std::ostringstream out;
    NdjsonWriter w(out);
    w.write_scan_start("/var", 1786097000, "abc", 16);
    std::string line = out.str();
    EXPECT_NE(line.find("\"type\":\"scan.start\""), std::string::npos);
    EXPECT_NE(line.find("\"root\":\"/var\""), std::string::npos);
    EXPECT_NE(line.find("\"workers\":16"), std::string::npos);
}

TEST(NdjsonWriter, WritesScanEndFrame) {
    std::ostringstream out;
    NdjsonWriter w(out);
    w.write_scan_end("abc", 100, 1000000, 500, 90, 10, false);
    EXPECT_NE(out.str().find("\"type\":\"scan.end\""), std::string::npos);
    EXPECT_NE(out.str().find("\"total_entries\":100"), std::string::npos);
    EXPECT_NE(out.str().find("\"cancelled\":false"), std::string::npos);
}
