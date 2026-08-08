#include "ndjson_writer.h"
#include <sstream>
#include <iomanip>

NdjsonWriter::NdjsonWriter(std::ostream& out) : out_(out) {}

std::string NdjsonWriter::escape_json(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 8);
    for (unsigned char c : s) {
        switch (c) {
            case '"':  out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            case '\b': out += "\\b"; break;
            case '\f': out += "\\f"; break;
            default:
                if (c < 0x20) {
                    static const char hex[] = "0123456789abcdef";
                    out += "\\u00";
                    out += hex[(c >> 4) & 0x0F];
                    out += hex[c & 0x0F];
                } else {
                    out += static_cast<char>(c);
                }
                break;
        }
    }
    return out;
}

void NdjsonWriter::write_scan_start(const std::string& root, int64_t started_at,
                                     const std::string& scan_id, int workers) {
    out_ << "{\"type\":\"scan.start\""
         << ",\"root\":\"" << escape_json(root) << "\""
         << ",\"started_at\":" << started_at
         << ",\"scan_id\":\"" << escape_json(scan_id) << "\""
         << ",\"workers\":" << workers
         << "}\n" << std::flush;
}

void NdjsonWriter::write_entry(const Entry& e) {
    out_ << "{\"type\":\"entry\""
         << ",\"path\":\"" << escape_json(e.path) << "\""
         << ",\"size\":" << e.size
         << ",\"type\":\"" << escape_json(e.type) << "\""
         << ",\"ext\":\"" << escape_json(e.ext) << "\""
         << ",\"mode\":" << e.mode
         << ",\"mtime\":" << e.mtime
         << ",\"inode\":" << e.inode
         << ",\"uid\":" << e.uid
         << ",\"gid\":" << e.gid
         << ",\"nlink\":" << e.nlink
         << ",\"cached\":" << (e.cached ? "true" : "false");
    if (e.type == "dir") {
        out_ << ",\"children\":" << e.children;
    }
    out_ << "}\n" << std::flush;
}

void NdjsonWriter::write_progress(int64_t scanned, int64_t dirs, int64_t bytes_so_far,
                                   int64_t elapsed_ms, int64_t eta_ms) {
    out_ << "{\"type\":\"progress\""
         << ",\"scanned\":" << scanned
         << ",\"dirs\":" << dirs
         << ",\"bytes_so_far\":" << bytes_so_far
         << ",\"elapsed_ms\":" << elapsed_ms
         << ",\"eta_ms\":" << eta_ms
         << "}\n" << std::flush;
}

void NdjsonWriter::write_warn(const std::string& path, const std::string& code,
                               const std::string& msg) {
    out_ << "{\"type\":\"warn\""
         << ",\"path\":\"" << escape_json(path) << "\""
         << ",\"code\":\"" << escape_json(code) << "\""
         << ",\"msg\":\"" << escape_json(msg) << "\""
         << "}\n" << std::flush;
}

void NdjsonWriter::write_scan_end(const std::string& scan_id, int64_t total_entries,
                                  int64_t total_bytes, int64_t elapsed_ms,
                                  int64_t cache_hits, int64_t cache_misses,
                                  bool cancelled) {
    out_ << "{\"type\":\"scan.end\""
         << ",\"scan_id\":\"" << escape_json(scan_id) << "\""
         << ",\"total_entries\":" << total_entries
         << ",\"total_bytes\":" << total_bytes
         << ",\"elapsed_ms\":" << elapsed_ms
         << ",\"cache_hits\":" << cache_hits
         << ",\"cache_misses\":" << cache_misses
         << ",\"cancelled\":" << (cancelled ? "true" : "false")
         << "}\n" << std::flush;
}
