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

def test_post_scan_returns_scan_id():
    with TestClient(app) as client:
        r = client.post("/scan", json={"root": "/tmp"},
                        headers={"Authorization": "Bearer dev-read"})
        assert r.status_code == 200
        assert "scan_id" in r.json()

def test_post_scan_rejects_without_token():
    with TestClient(app) as client:
        r = client.post("/scan", json={"root": "/tmp"})
        assert r.status_code == 401

def test_get_scan_status_returns_state():
    import time
    with TestClient(app) as client:
        r = client.post("/scan", json={"root": "/tmp"},
                        headers={"Authorization": "Bearer dev-read"})
        scan_id = r.json()["scan_id"]
        # Wait for completion
        r2 = None
        for _ in range(20):
            r2 = client.get(f"/scan/{scan_id}",
                            headers={"Authorization": "Bearer dev-read"})
            if r2.json()["finished"]:
                break
            time.sleep(0.1)
        assert r2.status_code == 200
        assert r2.json()["finished"] is True
