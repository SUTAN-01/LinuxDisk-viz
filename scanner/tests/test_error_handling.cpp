#include <gtest/gtest.h>
#include <sstream>
#include <string>
#include "walker.h"
#include "ndjson_writer.h"
#include "test_util.h"

using testutil::TestDir;

// Permission-denied directories must produce a "warn" frame. The POSIX
// permission model is used, so this test is Linux-only (skipped on Windows
// and when running as root, where chmod 000 is still bypassable).
TEST(ErrorHandling, WarnsOnPermissionDeniedDir) {
#ifdef _WIN32
    GTEST_SKIP() << "Permission test skipped on Windows";
#else
    if (geteuid() == 0) GTEST_SKIP() << "root skips permission tests";

    TestDir tmp("diskviz_perm_test");
    tmp.create_dir("noperm");
    tmp.create_file("noperm/secret.txt", "hidden");
    std::string noperm = testutil::join(tmp.path(), "noperm");
    chmod(noperm.c_str(), 0);

    std::ostringstream out;
    NdjsonWriter w(out);
    walk_and_stat(tmp.path(), w, "", 2, {});

    // Restore permissions so the temp tree can be cleaned up.
    chmod(noperm.c_str(), 0755);
    EXPECT_NE(out.str().find("\"type\":\"warn\""), std::string::npos);
#endif
}
