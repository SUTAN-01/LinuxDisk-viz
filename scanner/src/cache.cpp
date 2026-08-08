#include "cache.h"

#include <sqlite3.h>
#include <stdexcept>
#include <cstdio>
#include <string>

struct Cache::Impl {
    std::string path;
    sqlite3* db = nullptr;
    bool in_txn = false;
    sqlite3_stmt* lookup_stmt = nullptr;
    sqlite3_stmt* upsert_stmt = nullptr;

    void exec(const char* sql) {
        char* err = nullptr;
        int rc = sqlite3_exec(db, sql, nullptr, nullptr, &err);
        (void)rc;
        if (err) sqlite3_free(err);
    }

    void prepare_statements() {
        sqlite3_prepare_v2(db,
            "SELECT dev, inode, path_hash, path, size, mtime, mode, type, ext, "
            "uid, gid, nlink FROM cache WHERE dev=? AND inode=? AND mtime=? AND size=?",
            -1, &lookup_stmt, nullptr);
        sqlite3_prepare_v2(db,
            "INSERT OR REPLACE INTO cache (dev, inode, path_hash, path, size, "
            "mtime, mode, type, ext, uid, gid, nlink) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            -1, &upsert_stmt, nullptr);
    }

    void finalize_all() {
        if (lookup_stmt) { sqlite3_finalize(lookup_stmt); lookup_stmt = nullptr; }
        if (upsert_stmt) { sqlite3_finalize(upsert_stmt); upsert_stmt = nullptr; }
    }

    bool check_integrity() {
        sqlite3_stmt* stmt = nullptr;
        int rc = sqlite3_prepare_v2(db, "PRAGMA integrity_check", -1, &stmt, nullptr);
        if (rc != SQLITE_OK || !stmt) {
            if (stmt) sqlite3_finalize(stmt);
            return false;
        }
        rc = sqlite3_step(stmt);
        bool ok = false;
        if (rc == SQLITE_ROW) {
            const unsigned char* text = sqlite3_column_text(stmt, 0);
            if (text && std::string(reinterpret_cast<const char*>(text)) == "ok") {
                ok = true;
            }
        }
        sqlite3_finalize(stmt);
        return ok;
    }

    void reopen_fresh() {
        finalize_all();
        if (db) { sqlite3_close(db); db = nullptr; }
        std::remove(path.c_str());
        int rc = sqlite3_open(path.c_str(), &db);
        if (rc != SQLITE_OK) {
            if (db) { sqlite3_close(db); db = nullptr; }
            throw std::runtime_error("sqlite3_open failed on reopen");
        }
    }
};

Cache::Cache(const std::string& path) : impl_(new Impl()) {
    impl_->path = path;
}

Cache::~Cache() {
    close();
    delete impl_;
}

void Cache::open() {
    Impl& p = *impl_;
    int rc = sqlite3_open(p.path.c_str(), &p.db);
    if (rc != SQLITE_OK) {
        p.reopen_fresh();
    }

    if (!p.check_integrity()) {
        p.reopen_fresh();
    }

    p.exec("PRAGMA journal_mode=WAL");
    p.exec("PRAGMA synchronous=NORMAL");

    p.exec(
        "CREATE TABLE IF NOT EXISTS cache ("
        "dev INTEGER NOT NULL, "
        "inode INTEGER NOT NULL, "
        "path_hash INTEGER NOT NULL, "
        "path TEXT NOT NULL, "
        "size INTEGER NOT NULL, "
        "mtime INTEGER NOT NULL, "
        "mode INTEGER NOT NULL, "
        "type TEXT NOT NULL, "
        "ext TEXT NOT NULL, "
        "uid INTEGER NOT NULL, "
        "gid INTEGER NOT NULL, "
        "nlink INTEGER NOT NULL, "
        "PRIMARY KEY (dev, inode, path_hash))");
    p.exec("CREATE INDEX IF NOT EXISTS idx_cache_path ON cache(path)");

    p.prepare_statements();
}

std::optional<CacheEntry> Cache::lookup(int64_t dev, int64_t inode,
                                         int64_t mtime, int64_t size) {
    Impl& p = *impl_;
    if (!p.lookup_stmt) return std::nullopt;
    sqlite3_reset(p.lookup_stmt);
    sqlite3_bind_int64(p.lookup_stmt, 1, dev);
    sqlite3_bind_int64(p.lookup_stmt, 2, inode);
    sqlite3_bind_int64(p.lookup_stmt, 3, mtime);
    sqlite3_bind_int64(p.lookup_stmt, 4, size);
    int rc = sqlite3_step(p.lookup_stmt);
    if (rc != SQLITE_ROW) return std::nullopt;
    CacheEntry e{};
    e.dev = sqlite3_column_int64(p.lookup_stmt, 0);
    e.inode = sqlite3_column_int64(p.lookup_stmt, 1);
    e.path_hash = sqlite3_column_int64(p.lookup_stmt, 2);
    const unsigned char* path = sqlite3_column_text(p.lookup_stmt, 3);
    e.path = path ? reinterpret_cast<const char*>(path) : "";
    e.size = sqlite3_column_int64(p.lookup_stmt, 4);
    e.mtime = sqlite3_column_int64(p.lookup_stmt, 5);
    e.mode = sqlite3_column_int(p.lookup_stmt, 6);
    const unsigned char* type = sqlite3_column_text(p.lookup_stmt, 7);
    e.type = type ? reinterpret_cast<const char*>(type) : "";
    const unsigned char* ext = sqlite3_column_text(p.lookup_stmt, 8);
    e.ext = ext ? reinterpret_cast<const char*>(ext) : "";
    e.uid = sqlite3_column_int(p.lookup_stmt, 9);
    e.gid = sqlite3_column_int(p.lookup_stmt, 10);
    e.nlink = sqlite3_column_int(p.lookup_stmt, 11);
    return e;
}

void Cache::upsert(const CacheEntry& e) {
    Impl& p = *impl_;
    if (!p.upsert_stmt) return;
    if (!p.in_txn) {
        p.exec("BEGIN");
        p.in_txn = true;
    }
    sqlite3_reset(p.upsert_stmt);
    sqlite3_bind_int64(p.upsert_stmt, 1, e.dev);
    sqlite3_bind_int64(p.upsert_stmt, 2, e.inode);
    sqlite3_bind_int64(p.upsert_stmt, 3, e.path_hash);
    sqlite3_bind_text(p.upsert_stmt, 4, e.path.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int64(p.upsert_stmt, 5, e.size);
    sqlite3_bind_int64(p.upsert_stmt, 6, e.mtime);
    sqlite3_bind_int(p.upsert_stmt, 7, e.mode);
    sqlite3_bind_text(p.upsert_stmt, 8, e.type.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(p.upsert_stmt, 9, e.ext.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int(p.upsert_stmt, 10, e.uid);
    sqlite3_bind_int(p.upsert_stmt, 11, e.gid);
    sqlite3_bind_int(p.upsert_stmt, 12, e.nlink);
    sqlite3_step(p.upsert_stmt);
}

void Cache::flush_batch() {
    Impl& p = *impl_;
    if (p.in_txn) {
        p.exec("COMMIT");
        p.in_txn = false;
    }
}

void Cache::close() {
    Impl& p = *impl_;
    flush_batch();
    p.finalize_all();
    if (p.db) { sqlite3_close(p.db); p.db = nullptr; }
}
