#pragma once
#include <string>
#include <functional>
#include <vector>
#include <atomic>
#include <cstdint>

struct StatResult {
    bool ok;
    int64_t size;
    int32_t mode;
    int64_t mtime;
    int64_t inode;
    int32_t uid;
    int32_t gid;
    int32_t nlink;
    std::string err_code;
};

class StatPool {
public:
    explicit StatPool(int workers);
    void run(const std::vector<std::string>& paths,
             std::function<void(const std::string& path, const StatResult&)> callback);
private:
    int workers_;
};
