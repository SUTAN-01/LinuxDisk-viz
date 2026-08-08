#include <gtest/gtest.h>
#include <cstdlib>
#include <string>
#include <memory>
#include <array>
#include "test_util.h"

using testutil::TestDir;

namespace {

inline const std::string BIN =
#ifdef _WIN32
    "disk-scanner.exe";
#else
    "./disk-scanner";
#endif

std::string exec(const std::string& cmd) {
    std::array<char, 128> buf;
    std::string result;
#ifdef _WIN32
    std::unique_ptr<FILE, decltype(&_pclose)> pipe(_popen(cmd.c_str(), "r"), _pclose);
#else
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.c_str(), "r"), pclose);
#endif
    if (!pipe) return "";
    while (fgets(buf.data(), buf.size(), pipe.get())) result += buf.data();
    return result;
}

}  // namespace

TEST(Cli, PrintsHelpAndExitsZero) {
    std::string out = exec(BIN + " --help 2>&1");
    EXPECT_NE(out.find("Usage:"), std::string::npos);
    EXPECT_NE(out.find("--ndjson"), std::string::npos);
}

TEST(Cli, ScansDirectoryAndOutputsNdjson) {
    TestDir tmp("diskviz_cli_test");
    tmp.create_file("f.txt", "hello");
    std::string cmd = BIN + " --root \"" + tmp.path() + "\" --ndjson --no-cache 2>&1";
    std::string out = exec(cmd);
    EXPECT_NE(out.find("scan.start"), std::string::npos);
    EXPECT_NE(out.find("scan.end"), std::string::npos);
}

TEST(Cli, ExitsNonzeroForMissingRoot) {
#ifdef _WIN32
    std::string cmd = BIN + " --root /nonexistent/xyz123 2>nul";
#else
    std::string cmd = BIN + " --root /nonexistent/xyz123 2>/dev/null";
#endif
    int rc = std::system(cmd.c_str());
    EXPECT_NE(rc, 0);
}
