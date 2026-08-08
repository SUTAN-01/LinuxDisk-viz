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

async def _seed_scan(scan_id: str, tmp_path):
    store = ScanStore(tmp_path / f"{scan_id}.sqlite")
    await store.open()
    await store.insert_entry(scan_id, {
        "path": "/var/log/a.txt", "parent": "/var/log", "name": "a.txt",
        "size": 100, "type": "file", "ext": "txt", "mode": 33188, "mtime": 0,
        "inode": 1, "uid": 0, "gid": 0, "nlink": 1, "cached": False
    })
    await store.insert_entry(scan_id, {
        "path": "/var/log/b.txt", "parent": "/var/log", "name": "b.txt",
        "size": 200, "type": "file", "ext": "txt", "mode": 33188, "mtime": 0,
        "inode": 2, "uid": 0, "gid": 0, "nlink": 1, "cached": False
    })
    await store.flush()
    app.state.scan_manager._scans[scan_id] = RunningScan(
        scan_id=scan_id, root="/var", proc=None, started_at=0, store=store, finished=True
    )

def test_get_tree_returns_children(tmp_path):
    asyncio.run(_seed_scan("t1", tmp_path))
    with TestClient(app) as client:
        r = client.get("/tree/t1", params={"path": "/var/log"},
                       headers={"Authorization": "Bearer dev-read"})
    assert r.status_code == 200
    data = r.json()
    assert "entries" in data
    assert len(data["entries"]) == 2

def test_get_tree_404_for_unknown_scan():
    with TestClient(app) as client:
        r = client.get("/tree/nonexistent", params={"path": "/"},
                       headers={"Authorization": "Bearer dev-read"})
    assert r.status_code == 404

def test_get_tree_rejects_no_token(tmp_path):
    asyncio.run(_seed_scan("t2", tmp_path))
    with TestClient(app) as client:
        r = client.get("/tree/t2", params={"path": "/var/log"})
    assert r.status_code == 401
