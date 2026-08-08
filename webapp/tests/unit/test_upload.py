import hashlib
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from diskviz_api.main import app
from diskviz_api.services.scanner_runner import ScanManager, RunningScan
from diskviz_api.services.upload import UploadManager

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
    app.state.upload_manager = UploadManager(scans_dir=tmp_path)
    yield


def test_create_upload_session(tmp_path):
    target = tmp_path / "incoming"
    body = b"hello world"
    with TestClient(app) as client:
        r = client.post("/upload",
                        params={"path": str(target)},
                        headers={"Authorization": "Bearer dev-write",
                                 "Upload-Length": str(len(body))})
    assert r.status_code == 200
    data = r.json()
    assert "upload_id" in data
    assert data["length"] == len(body)
    # Session should exist in the manager
    sess = app.state.upload_manager.get_status(data["upload_id"])
    assert sess["target_dir"] == str(target)
    assert sess["length"] == len(body)
    assert sess["offset"] == 0
    assert sess["completed"] is False


def test_patch_and_complete_lands_file(tmp_path):
    target = tmp_path / "incoming"
    body = b"hello world"
    with TestClient(app) as client:
        # create
        r = client.post("/upload",
                        params={"path": str(target)},
                        headers={"Authorization": "Bearer dev-write",
                                 "Upload-Length": str(len(body))})
        assert r.status_code == 200
        upload_id = r.json()["upload_id"]
        # patch
        r2 = client.patch(f"/upload/{upload_id}",
                          headers={"Authorization": "Bearer dev-write",
                                   "Upload-Offset": "0"},
                          content=body)
        assert r2.status_code == 200
        assert r2.json()["offset"] == len(body)
        # complete
        r3 = client.post(f"/upload/{upload_id}/complete",
                         params={"filename": "test.txt"},
                         headers={"Authorization": "Bearer dev-write"})
        assert r3.status_code == 200
        final = Path(r3.json()["final_path"])
        assert final.exists()
        assert final.read_bytes() == body
        assert final.name == "test.txt"
        assert final.parent == target


def test_create_rejects_missing_length_header(tmp_path):
    target = tmp_path / "incoming"
    with TestClient(app) as client:
        r = client.post("/upload",
                        params={"path": str(target)},
                        headers={"Authorization": "Bearer dev-write"})
    assert r.status_code == 400


def test_patch_offset_mismatch_returns_409(tmp_path):
    target = tmp_path / "incoming"
    body = b"hello world"
    with TestClient(app) as client:
        r = client.post("/upload",
                        params={"path": str(target)},
                        headers={"Authorization": "Bearer dev-write",
                                 "Upload-Length": str(len(body))})
        assert r.status_code == 200
        upload_id = r.json()["upload_id"]
        # offset 5 when expected 0 -> 409
        r2 = client.patch(f"/upload/{upload_id}",
                          headers={"Authorization": "Bearer dev-write",
                                   "Upload-Offset": "5"},
                          content=body)
        assert r2.status_code == 409


def test_complete_rejects_path_traversal_filename(tmp_path):
    target = tmp_path / "incoming"
    body = b"hello world"
    with TestClient(app) as client:
        r = client.post("/upload",
                        params={"path": str(target)},
                        headers={"Authorization": "Bearer dev-write",
                                 "Upload-Length": str(len(body))})
        assert r.status_code == 200
        upload_id = r.json()["upload_id"]
        r2 = client.patch(f"/upload/{upload_id}",
                          headers={"Authorization": "Bearer dev-write",
                                   "Upload-Offset": "0"},
                          content=body)
        assert r2.status_code == 200
        r3 = client.post(f"/upload/{upload_id}/complete",
                         params={"filename": "../evil"},
                         headers={"Authorization": "Bearer dev-write"})
    assert r3.status_code == 400


def test_complete_unknown_id_returns_404():
    with TestClient(app) as client:
        r = client.post("/upload/up-nonexistent/complete",
                        params={"filename": "x.txt"},
                        headers={"Authorization": "Bearer dev-write"})
    assert r.status_code == 404


def test_patch_unknown_id_returns_404():
    with TestClient(app) as client:
        r = client.patch("/upload/up-nonexistent",
                         headers={"Authorization": "Bearer dev-write",
                                  "Upload-Offset": "0"},
                         content=b"x")
    assert r.status_code == 404
