import time
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from diskviz_api.main import app
from diskviz_api.services.scanner_runner import ScanManager, RunningScan
from diskviz_api.services.upload import UploadManager

mock_scanner = str(Path(__file__).parent.parent / "fixtures" / "mock_scanner.py")


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


def _full_upload(client, target, body=b"hello world"):
    """Create + patch full body. Returns upload_id."""
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
    return upload_id


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


def test_complete_rejects_incomplete_upload(tmp_path):
    target = tmp_path / "incoming"
    with TestClient(app) as client:
        r = client.post("/upload",
                        params={"path": str(target)},
                        headers={"Authorization": "Bearer dev-write",
                                 "Upload-Length": "10"})
        assert r.status_code == 200
        upload_id = r.json()["upload_id"]
        r2 = client.patch(f"/upload/{upload_id}",
                          headers={"Authorization": "Bearer dev-write",
                                   "Upload-Offset": "0"},
                          content=b"hello")  # only 5 of 10 bytes
        assert r2.status_code == 200
        r3 = client.post(f"/upload/{upload_id}/complete",
                         params={"filename": "x.txt"},
                         headers={"Authorization": "Bearer dev-write"})
        assert r3.status_code == 409


def test_complete_rejects_backslash_traversal(tmp_path):
    target = tmp_path / "incoming"
    with TestClient(app) as client:
        upload_id = _full_upload(client, target)
        r = client.post(f"/upload/{upload_id}/complete",
                        params={"filename": "..\\evil"},
                        headers={"Authorization": "Bearer dev-write"})
        assert r.status_code == 400


def test_complete_rejects_null_byte_filename(tmp_path):
    target = tmp_path / "incoming"
    with TestClient(app) as client:
        upload_id = _full_upload(client, target)
        r = client.post(f"/upload/{upload_id}/complete",
                        params={"filename": "a\0b"},
                        headers={"Authorization": "Bearer dev-write"})
        assert r.status_code == 400


def test_complete_rejects_empty_filename(tmp_path):
    target = tmp_path / "incoming"
    with TestClient(app) as client:
        upload_id = _full_upload(client, target)
        r = client.post(f"/upload/{upload_id}/complete",
                        params={"filename": ""},
                        headers={"Authorization": "Bearer dev-write"})
        assert r.status_code == 400


def test_complete_rejects_dot_basename(tmp_path):
    target = tmp_path / "incoming"
    with TestClient(app) as client:
        upload_id = _full_upload(client, target)
        r = client.post(f"/upload/{upload_id}/complete",
                        params={"filename": "."},
                        headers={"Authorization": "Bearer dev-write"})
        assert r.status_code == 400


def test_append_to_completed_returns_409(tmp_path):
    target = tmp_path / "incoming"
    body = b"hello world"
    with TestClient(app) as client:
        upload_id = _full_upload(client, target, body)
        r = client.post(f"/upload/{upload_id}/complete",
                        params={"filename": "x.txt"},
                        headers={"Authorization": "Bearer dev-write"})
        assert r.status_code == 200
        # patch again after completion -> 409
        r2 = client.patch(f"/upload/{upload_id}",
                          headers={"Authorization": "Bearer dev-write",
                                   "Upload-Offset": str(len(body))},
                          content=b"extra")
        assert r2.status_code == 409


def test_cleanup_expired_removes_old_sessions(tmp_path):
    mgr = app.state.upload_manager
    uid = mgr.create(str(tmp_path / "incoming"), length=10)
    tmp_file = Path(mgr.get_status(uid)["tmp_path"])
    assert tmp_file.exists()
    # backdate the session well past the ttl
    mgr._sessions[uid]["created_at"] = time.time() - 3600
    removed = mgr.cleanup_expired(ttl_seconds=60)
    assert removed == 1
    assert uid not in mgr._sessions
    assert not tmp_file.exists()
