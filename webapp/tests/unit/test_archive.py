import hashlib
import tarfile
import time
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from diskviz_api.main import app
from diskviz_api.services.scanner_runner import ScanManager, RunningScan

mock_scanner = str(Path(__file__).parent.parent / "fixtures" / "mock_scanner.py")
CONFIRM = hashlib.sha256(b"dev-write").hexdigest()


@pytest.fixture(autouse=True)
def setup_managers(tmp_path):
    app.state.scan_manager = ScanManager(
        scanner_binary="D:\\anaconda3\\python.exe",
        scanner_args=[mock_scanner],
        cache_path=str(tmp_path / "c.sqlite"),
        scans_dir=tmp_path,
    )
    app.state.scan_manager._scans["s1"] = RunningScan(
        scan_id="s1", root=str(tmp_path), proc=None, started_at=0,
        store=None, finished=True,
    )
    from diskviz_api.services.archive import ArchiveManager
    app.state.archive_manager = ArchiveManager(scans_dir=tmp_path)
    yield


def _poll_done(client, job_id, timeout=2.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        r = client.get(f"/archive/{job_id}",
                       headers={"Authorization": "Bearer dev-read"})
        last = r
        if r.status_code == 200 and r.json().get("status") == "done":
            return r
        time.sleep(0.05)
    return last


def test_pack_creates_targz_with_content(tmp_path):
    f1 = tmp_path / "a.txt"; f1.write_text("hello")
    f2 = tmp_path / "b.txt"; f2.write_text("world")
    with TestClient(app) as client:
        r = client.post("/archive/pack",
                        json={"paths": [str(f1), str(f2)], "format": "tar.gz",
                              "confirm_token": CONFIRM},
                        headers={"Authorization": "Bearer dev-write"})
        assert r.status_code == 200
        job_id = r.json()["job_id"]
        r = _poll_done(client, job_id)
        assert r is not None and r.status_code == 200
        assert r.json()["status"] == "done"
        out = Path(r.json()["out_path"])
        assert out.exists()
        with tarfile.open(out, "r:gz") as tar:
            names = sorted(tar.getnames())
        assert names == ["a.txt", "b.txt"]


def test_unknown_job_returns_404():
    with TestClient(app) as client:
        r = client.get("/archive/nonexistent",
                       headers={"Authorization": "Bearer dev-read"})
    assert r.status_code == 404


def test_pack_without_confirm_returns_403(tmp_path):
    f = tmp_path / "c.txt"; f.write_text("c")
    with TestClient(app) as client:
        r = client.post("/archive/pack",
                        json={"paths": [str(f)], "format": "tar.gz",
                              "confirm_token": ""},
                        headers={"Authorization": "Bearer dev-write"})
    assert r.status_code == 403


def test_pack_rejects_read_token(tmp_path):
    f = tmp_path / "d.txt"; f.write_text("d")
    with TestClient(app) as client:
        r = client.post("/archive/pack",
                        json={"paths": [str(f)], "format": "tar.gz",
                              "confirm_token": CONFIRM},
                        headers={"Authorization": "Bearer dev-read"})
    assert r.status_code == 401


def test_pack_creates_zip_with_content(tmp_path):
    f1 = tmp_path / "x.txt"; f1.write_text("xx")
    with TestClient(app) as client:
        r = client.post("/archive/pack",
                        json={"paths": [str(f1)], "format": "zip",
                              "confirm_token": CONFIRM},
                        headers={"Authorization": "Bearer dev-write"})
        assert r.status_code == 200
        job_id = r.json()["job_id"]
        r = _poll_done(client, job_id)
        assert r is not None and r.status_code == 200
        assert r.json()["status"] == "done"
        out = Path(r.json()["out_path"])
        assert out.exists()
        with zipfile.ZipFile(out) as zf:
            names = sorted(zf.namelist())
        assert names == ["x.txt"]
