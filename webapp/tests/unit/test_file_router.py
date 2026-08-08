import asyncio
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from diskviz_api.main import app
from diskviz_api.services.scanner_runner import ScanManager, RunningScan
from diskviz_api.services.scan_store import ScanStore

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

async def _seed(scan_id, tmp_path):
    store = ScanStore(tmp_path / f"{scan_id}.sqlite")
    await store.open()
    (tmp_path / "hello.txt").write_text("hello world")
    await store.insert_entry(scan_id, {
        "path": str(tmp_path / "hello.txt"), "parent": str(tmp_path),
        "name": "hello.txt", "size": 11, "type": "file", "ext": "txt",
        "mode": 33188, "mtime": 0, "inode": 0, "uid": 0, "gid": 0,
        "nlink": 1, "cached": False
    })
    await store.flush()
    app.state.scan_manager._scans[scan_id] = RunningScan(
        scan_id=scan_id, root=str(tmp_path), proc=None, started_at=0,
        store=store, finished=True
    )

def test_get_file_metadata(tmp_path):
    asyncio.run(_seed("f1", tmp_path))
    with TestClient(app) as client:
        r = client.get("/file/f1", params={"path": str(tmp_path / "hello.txt")},
                       headers={"Authorization": "Bearer dev-read"})
    assert r.status_code == 200
    assert r.json()["name"] == "hello.txt"
    assert r.json()["size"] == 11

def test_download_file_content(tmp_path):
    asyncio.run(_seed("f2", tmp_path))
    with TestClient(app) as client:
        r = client.get("/file/f2/content", params={"path": str(tmp_path / "hello.txt")},
                       headers={"Authorization": "Bearer dev-read"})
    assert r.status_code == 200
    assert r.content == b"hello world"

def test_file_router_rejects_no_token(tmp_path):
    asyncio.run(_seed("f3", tmp_path))
    with TestClient(app) as client:
        r = client.get("/file/f3", params={"path": str(tmp_path / "hello.txt")})
    assert r.status_code == 401
