#include "stat_pool.h"
#include "concurrentqueue.h"

#include <thread>
#include <atomic>
#include <utility>
#include <vector>
#include <cerrno>
#include <sys/stat.h>

StatPool::StatPool(int workers) : workers_(workers > 0 ? workers : 1) {}

void StatPool::run(const std::vector<std::string>& paths,
                   std::function<void(const std::string& path, const StatResult&)> callback) {
    if (paths.empty()) return;

    moodycamel::ConcurrentQueue<std::string> in_q;
    moodycamel::ConcurrentQueue<std::pair<std::string, StatResult>> out_q;

    for (const auto& p : paths) {
        in_q.enqueue(p);
    }

    const int total = static_cast<int>(paths.size());
    const int nw = workers_;

    std::vector<std::thread> threads;
    threads.reserve(nw);
    for (int i = 0; i < nw; ++i) {
        threads.emplace_back([&]() {
            std::string path;
            while (in_q.try_dequeue(path)) {
                StatResult r{};
                struct stat st;
                if (stat(path.c_str(), &st) == 0) {
                    r.ok = true;
                    r.size = static_cast<int64_t>(st.st_size);
                    r.mode = static_cast<int32_t>(st.st_mode);
                    r.mtime = static_cast<int64_t>(st.st_mtime);
                    r.inode = static_cast<int64_t>(st.st_ino);
                    r.uid = static_cast<int32_t>(st.st_uid);
                    r.gid = static_cast<int32_t>(st.st_gid);
                    r.nlink = static_cast<int32_t>(st.st_nlink);
                    r.err_code = "";
                } else {
                    r.ok = false;
                    switch (errno) {
                        case EACCES: r.err_code = "EACCES"; break;
                        case ENOENT: r.err_code = "ENOENT"; break;
                        case EIO:    r.err_code = "EIO"; break;
                        default:     r.err_code = "EIO"; break;
                    }
                }
                out_q.enqueue(std::make_pair(path, r));
            }
        });
    }

    // Main thread consumes results until all paths have been processed.
    int consumed = 0;
    while (consumed < total) {
        std::pair<std::string, StatResult> result;
        if (out_q.try_dequeue(result)) {
            callback(result.first, result.second);
            ++consumed;
        } else {
            std::this_thread::yield();
        }
    }

    for (auto& t : threads) {
        t.join();
    }
}
