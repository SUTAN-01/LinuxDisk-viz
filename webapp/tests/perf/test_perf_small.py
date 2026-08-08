"""Performance benchmarks for the small dataset (100k files).

Run:
    bash ../../scripts/gen_perf_dataset.sh small /tmp/diskviz-perf
    DISKVIZ_PERF_DIR=/tmp/diskviz-perf pytest tests/perf -v
"""
from __future__ import annotations

import time


def test_first_scan_100k_files_under_3s(scan_client, perf_dir):
    start = time.monotonic()
    scan_id = scan_client.start_scan(perf_dir)
    scan_client.wait_done(scan_id, timeout=30)
    elapsed = time.monotonic() - start
    assert elapsed < 3.0, f"first scan took {elapsed:.2f}s (limit 3.0s)"


def test_drilldown_query_under_50ms(scan_client, perf_dir):
    scan_id = scan_client.start_scan_and_wait(perf_dir)
    elapsed = scan_client.measure_get_tree(scan_id, path=perf_dir)
    assert elapsed < 0.05, f"drilldown took {elapsed*1000:.1f}ms (limit 50ms)"
