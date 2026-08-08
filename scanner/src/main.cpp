#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <thread>
#include <chrono>
#include <ctime>
#include <cstdint>
#include <cstdlib>
#include <sys/stat.h>

#include "walker.h"
#include "ndjson_writer.h"

#ifdef _WIN32
#include <process.h>
#define DISKVIZ_GETPID() _getpid()
#else
#include <unistd.h>
#define DISKVIZ_GETPID() getpid()
#endif

namespace {

void print_usage() {
    std::cout <<
        "Usage: disk-scanner [options]\n"
        "\n"
        "Scan a directory tree and emit NDJSON (one JSON object per line) to stdout.\n"
        "\n"
        "Options:\n"
        "  --root PATH          Directory to scan (default: .)\n"
        "  --ndjson             Emit NDJSON to stdout (default)\n"
        "  --sqlite PATH        Write results to a SQLite DB (v1: parsed, not yet wired)\n"
        "  --quiet              Suppress stdout output\n"
        "  --workers N          Stat worker threads (default: 2 * hardware_concurrency)\n"
        "  --cache PATH         Cache DB path (default: /var/lib/diskviz/cache.sqlite)\n"
        "  --no-cache           Disable the cache\n"
        "  --exclude GLOB       Exclude basename matching glob (repeatable)\n"
        "  --progress-every N   Emit a progress frame every N entries (default: 1000)\n"
        "  --max-depth N        Maximum descent depth\n"
        "  --follow-symlinks    Follow symlinks instead of treating them as links\n"
        "  --version            Print version and exit\n"
        "  --help               Print this help and exit\n";
}

}  // namespace

int main(int argc, char** argv) {
    std::string root = ".";
    bool ndjson = true;
    std::string sqlite_path;
    bool quiet = false;
    int workers = 0;
    std::string cache_path = "/var/lib/diskviz/cache.sqlite";
    bool no_cache = false;
    std::vector<std::string> excludes;
    int progress_every = 1000;
    int max_depth = 0;
    bool follow_symlinks = false;

    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--help" || a == "-h") {
            print_usage();
            return 0;
        } else if (a == "--version") {
            std::cout << "disk-scanner 0.1.0\n";
            return 0;
        } else if (a == "--root") {
            if (++i >= argc) { std::cerr << "error: --root requires a path\n"; return 2; }
            root = argv[i];
        } else if (a == "--ndjson") {
            ndjson = true;
        } else if (a == "--sqlite") {
            if (++i >= argc) { std::cerr << "error: --sqlite requires a path\n"; return 2; }
            sqlite_path = argv[i];
        } else if (a == "--quiet") {
            quiet = true;
        } else if (a == "--workers") {
            if (++i >= argc) { std::cerr << "error: --workers requires a number\n"; return 2; }
            workers = std::atoi(argv[i]);
        } else if (a == "--cache") {
            if (++i >= argc) { std::cerr << "error: --cache requires a path\n"; return 2; }
            cache_path = argv[i];
        } else if (a == "--no-cache") {
            no_cache = true;
        } else if (a == "--exclude") {
            if (++i >= argc) { std::cerr << "error: --exclude requires a glob\n"; return 2; }
            excludes.push_back(argv[i]);
        } else if (a == "--progress-every") {
            if (++i >= argc) { std::cerr << "error: --progress-every requires a number\n"; return 2; }
            progress_every = std::atoi(argv[i]);
        } else if (a == "--max-depth") {
            if (++i >= argc) { std::cerr << "error: --max-depth requires a number\n"; return 2; }
            max_depth = std::atoi(argv[i]);
        } else if (a == "--follow-symlinks") {
            follow_symlinks = true;
        } else {
            std::cerr << "error: unknown argument: " << a << "\n";
            return 2;
        }
    }

    // Parsed but not yet wired into walk_and_stat (v1).
    (void)ndjson;
    (void)sqlite_path;
    (void)progress_every;
    (void)max_depth;
    (void)follow_symlinks;

    // Validate root exists.
    struct stat st;
    if (stat(root.c_str(), &st) != 0) {
        std::cerr << "error: root does not exist: " << root << "\n";
        return 2;
    }

    // Default workers = 2 * hardware_concurrency.
    if (workers <= 0) {
        unsigned hc = std::thread::hardware_concurrency();
        workers = static_cast<int>((hc > 0 ? hc : 4) * 2);
    }

    std::string effective_cache = no_cache ? std::string() : cache_path;
    std::string scan_id = "scan-" + std::to_string(DISKVIZ_GETPID());
    int64_t started_at = static_cast<int64_t>(std::time(nullptr));

    auto t_start = std::chrono::steady_clock::now();

    if (quiet) {
        // Discard output to a sink that is never read.
        std::ostringstream sink;
        NdjsonWriter w(sink);
        walk_and_stat(root, w, effective_cache, workers, excludes);
    } else {
        NdjsonWriter w(std::cout);
        w.write_scan_start(root, started_at, scan_id, workers);
        auto r = walk_and_stat(root, w, effective_cache, workers, excludes);
        auto t_end = std::chrono::steady_clock::now();
        int64_t elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            t_end - t_start).count();
        w.write_scan_end(scan_id, r.total_entries, r.total_bytes, elapsed_ms,
                         r.cache_hits, r.cache_misses, false);
    }

    return 0;
}
