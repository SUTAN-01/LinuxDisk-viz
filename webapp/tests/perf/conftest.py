"""Fixtures for performance tests.

Requires a generated dataset and the C++ scanner binary:
    bash ../../scripts/gen_perf_dataset.sh small /tmp/diskviz-perf
    DISKVIZ_PERF_DIR=/tmp/diskviz-perf pytest tests/perf -v
"""
from __future__ import annotations

import os
import time

import pytest
from fastapi.testclient import TestClient

from diskviz_api.main import app


@pytest.fixture(scope="session")
def perf_dir():
    d = os.environ.get("DISKVIZ_PERF_DIR")
    if not d:
        pytest.skip("set DISKVIZ_PERF_DIR to run perf tests")
    return d


@pytest.fixture
def scan_client(perf_dir):
    client = TestClient(app)
    headers = {"Authorization": "Bearer dev-read"}

    class _ScanClient:
        def start_scan(self, root: str) -> str:
            r = client.post("/scan", json={"root": root}, headers=headers)
            r.raise_for_status()
            return r.json()["scan_id"]

        def wait_done(self, scan_id: str, timeout: float = 30.0) -> None:
            deadline = time.time() + timeout
            while time.time() < deadline:
                r = client.get(f"/scan/{scan_id}", headers=headers)
                r.raise_for_status()
                if r.json().get("finished"):
                    return
                time.sleep(0.1)
            raise TimeoutError(f"scan {scan_id} did not finish in {timeout}s")

        def start_scan_and_wait(self, root: str, timeout: float = 30.0) -> str:
            sid = self.start_scan(root)
            self.wait_done(sid, timeout)
            return sid

        def measure_get_tree(self, scan_id: str, path: str) -> float:
            t0 = time.monotonic()
            r = client.get(
                f"/tree/{scan_id}",
                params={"path": path},
                headers=headers,
            )
            r.raise_for_status()
            return time.monotonic() - t0

    return _ScanClient()
