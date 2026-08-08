#pragma once
#include <string>
#include <optional>
#include <cstdint>

struct CacheEntry {
    int64_t dev;
    int64_t inode;
    int64_t path_hash;
    std::string path;
    int64_t size;
    int64_t mtime;
    int32_t mode;
    std::string type;
    std::string ext;
    int32_t uid;
    int32_t gid;
    int32_t nlink;
};

class Cache {
public:
    explicit Cache(const std::string& path);
    ~Cache();
    void open();
    std::optional<CacheEntry> lookup(int64_t dev, int64_t inode, int64_t mtime, int64_t size);
    void upsert(const CacheEntry& e);
    void flush_batch();
    void close();
private:
    struct Impl;
    Impl* impl_;
};
