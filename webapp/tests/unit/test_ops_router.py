import hashlib
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from diskviz_api.main import app
from diskviz_api.services.scanner_runner import ScanManager, RunningScan

mock_scanner = str(Path(__file__).parent.parent / "fixtures" / "mock_scanner.py")
CONFIRM = hashlib.sha256(b"dev-write").hexdigest()

@pytest.fixture(autouse=True)
def setup_manager(tmp_path):
    app.state.scan_manager = ScanManager(
        scanner_binary="D:\\anaconda3\\python.exe",
        scanner_args=[mock_scanner],
        cache_path=str(tmp_path / "c.sqlite"),
        scans_dir=tmp_path
    )
    yield

def _setup_scan(tmp_path):
    app.state.scan_manager._scans["s1"] = RunningScan(
        scan_id="s1", root=str(tmp_path), proc=None, started_at=0,
        store=None, finished=True
    )

def test_delete_without_confirm_returns_403(tmp_path):
    _setup_scan(tmp_path)
    f = tmp_path / "x.txt"; f.write_text("x")
    with TestClient(app) as client:
        r = client.post("/ops/delete",
                        json={"paths": [str(f)], "mode": "permanent", "confirm_token": ""},
                        headers={"Authorization": "Bearer dev-write"})
    assert r.status_code == 403

def test_delete_with_confirm_removes_file(tmp_path):
    _setup_scan(tmp_path)
    f = tmp_path / "y.txt"; f.write_text("y")
    with TestClient(app) as client:
        r = client.post("/ops/delete",
                        json={"paths": [str(f)], "mode": "permanent",
                              "confirm_token": CONFIRM},
                        headers={"Authorization": "Bearer dev-write"})
    assert r.status_code == 200
    assert r.json()["results"][0]["ok"]
    assert not f.exists()

def test_delete_rejects_read_token(tmp_path):
    _setup_scan(tmp_path)
    with TestClient(app) as client:
        r = client.post("/ops/delete",
                        json={"paths": [str(tmp_path)], "mode": "permanent",
                              "confirm_token": CONFIRM},
                        headers={"Authorization": "Bearer dev-read"})
    assert r.status_code == 401

def test_move_with_confirm(tmp_path):
    _setup_scan(tmp_path)
    f = tmp_path / "src.txt"; f.write_text("src")
    dst = tmp_path / "subdir"; dst.mkdir()
    with TestClient(app) as client:
        r = client.post("/ops/move",
                        json={"src_paths": [str(f)], "dst_dir": str(dst),
                              "confirm_token": CONFIRM},
                        headers={"Authorization": "Bearer dev-write"})
    assert r.status_code == 200
    assert (dst / "src.txt").exists()
    assert not f.exists()

def test_mkdir_with_confirm(tmp_path):
    _setup_scan(tmp_path)
    new_dir = tmp_path / "newdir"
    with TestClient(app) as client:
        r = client.post("/ops/mkdir",
                        json={"path": str(new_dir), "confirm_token": CONFIRM},
                        headers={"Authorization": "Bearer dev-write"})
    assert r.status_code == 200
    assert new_dir.exists()
