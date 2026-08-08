#pragma once
#include <string>
#include <cstdint>
#include <ostream>

struct Entry {
    std::string path;
    int64_t size;
    std::string type;       // file|dir|link|other
    std::string ext;
    int32_t mode;
    int64_t mtime;
    int64_t inode;
    int32_t uid;
    int32_t gid;
    int32_t nlink;
    bool cached;
    int64_t children = 0;
};

class NdjsonWriter {
public:
    explicit NdjsonWriter(std::ostream& out);
    void write_scan_start(const std::string& root, int64_t started_at,
                          const std::string& scan_id, int workers);
    void write_entry(const Entry& e);
    void write_progress(int64_t scanned, int64_t dirs, int64_t bytes_so_far,
                        int64_t elapsed_ms, int64_t eta_ms);
    void write_warn(const std::string& path, const std::string& code, const std::string& msg);
    void write_scan_end(const std::string& scan_id, int64_t total_entries,
                        int64_t total_bytes, int64_t elapsed_ms,
                        int64_t cache_hits, int64_t cache_misses, bool cancelled = false);
private:
    std::ostream& out_;
    static std::string escape_json(const std::string& s);
};
