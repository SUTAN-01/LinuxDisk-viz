#pragma once
// Portable test helpers that avoid std::filesystem (g++ 8.1.0's <filesystem>
// path::operator/= is buggy on MinGW: it uses operator!= on paths which is
// not defined). Used by walker / stat_pool / cache tests for temp tree setup.

#include <string>
#include <fstream>
#include <cstdio>
#include <cstdlib>
#include <sys/stat.h>
#include <sys/types.h>

#ifdef _WIN32
#include <direct.h>
#define DISKVIZ_MKDIR(p) _mkdir(p)
#define DISKVIZ_SEP "\\"
#else
#include <unistd.h>
#define DISKVIZ_MKDIR(p) mkdir((p), 0755)
#define DISKVIZ_SEP "/"
#endif

namespace testutil {

inline std::string temp_dir() {
    const char* t = std::getenv("TEMP");
    if (!t) t = std::getenv("TMP");
    if (!t) t = "/tmp";
    return std::string(t);
}

inline std::string join(const std::string& a, const std::string& b) {
    return a + DISKVIZ_SEP + b;
}

template<typename... Args>
inline std::string join(const std::string& a, const std::string& b, Args... rest) {
    return join(join(a, b), rest...);
}

inline bool make_dir(const std::string& p) {
    return DISKVIZ_MKDIR(p.c_str()) == 0;
}

inline void make_file(const std::string& p, const std::string& content) {
    std::ofstream f(p);
    f << content;
}

inline bool path_is_dir(const std::string& p) {
    struct stat st;
    return stat(p.c_str(), &st) == 0 && (st.st_mode & S_IFMT) == S_IFDIR;
}

// Recursively remove a directory tree (or single file). Idempotent: a missing
// path is not an error.
inline void remove_tree(const std::string& p) {
#ifdef _WIN32
    std::string cmd = "rmdir /s /q \"" + p + "\" >nul 2>nul";
#else
    std::string cmd = "rm -rf \"" + p + "\"";
#endif
    // Also try unlink in case p is a regular file (rmdir fails on files).
    std::remove(p.c_str());
    std::system(cmd.c_str());
}

}  // namespace testutil
