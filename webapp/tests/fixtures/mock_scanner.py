#!/usr/bin/env python3
"""Mock disk-scanner that outputs NDJSON."""
import sys
import json
import time

root = "."
for i, a in enumerate(sys.argv):
    if a == "--root" and i + 1 < len(sys.argv):
        root = sys.argv[i + 1]

print(json.dumps({"type": "scan.start", "root": root, "started_at": int(time.time()),
                  "scan_id": "mock", "workers": 4}))
for i in range(3):
    print(json.dumps({"type": "entry", "path": f"{root}/f{i}.txt", "size": 100 * (i + 1),
                      "mode": 33188, "mtime": 1000, "inode": i, "nlink": 1,
                      "uid": 0, "gid": 0, "ext": "txt", "type": "file", "cached": False}))
print(json.dumps({"type": "progress", "scanned": 3, "dirs": 0, "bytes_so_far": 600,
                  "elapsed_ms": 10, "eta_ms": 0}))
print(json.dumps({"type": "scan.end", "scan_id": "mock", "total_entries": 3,
                  "total_bytes": 600, "elapsed_ms": 10, "cache_hits": 0, "cache_misses": 3}))
