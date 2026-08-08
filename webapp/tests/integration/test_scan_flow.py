import time
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from diskviz_api.main import app
from diskviz_api.services.scanner_runner import ScanManager

mock_scanner = str(Path(__file__).parent.parent / "fixtures" / "mock_scanner.py")

@pytest.fixture(autouse=True)
def setup_manager(tmp_path):
    app.state.scan_manager = ScanManager(
        scanner_binary="D:\\anaconda3\\python.exe",
        scanner_args=[mock_scanner],
        cache_path=str(tmp_path / "c.sqlite"),
        scans_dir=tmp_path
    )
    yield

def test_full_scan_flow(tmp_path):
    # Prepare test data (the mock scanner ignores real files but uses root for entry paths)
    root = str(tmp_path)
    (tmp_path / "f1.txt").write_text("hello")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "f2.txt").write_text("world!")

    with TestClient(app) as client:
        # Start scan
        r = client.post("/scan", json={"root": root},
                        headers={"Authorization": "Bearer dev-read"})
        assert r.status_code == 200
        scan_id = r.json()["scan_id"]

        # Wait for completion (poll up to ~3s)
        r2 = None
        for _ in range(30):
            r2 = client.get(f"/scan/{scan_id}",
                            headers={"Authorization": "Bearer dev-read"})
            if r2.json().get("finished"):
                break
            time.sleep(0.1)
        assert r2 is not None
        assert r2.status_code == 200
        assert r2.json()["finished"] is True

        # Query tree — entries' parent == root (mock scanner emits {root}/f{i}.txt)
        r3 = client.get(f"/tree/{scan_id}", params={"path": root},
                        headers={"Authorization": "Bearer dev-read"})
        assert r3.status_code == 200
        entries = r3.json().get("entries", [])
        assert len(entries) > 0
        # mock scanner emits 3 entries (f0/f1/f2.txt) all with parent == root
        assert len(entries) == 3

        # Query top-large report
        r4 = client.get(f"/reports/top-large/{scan_id}",
                        params={"limit": 10},
                        headers={"Authorization": "Bearer dev-read"})
        assert r4.status_code == 200
        assert r4.json()["count"] == 3
