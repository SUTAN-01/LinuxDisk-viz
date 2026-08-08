import pytest
from pathlib import Path
from diskviz_api.services.scan_store import ScanStore

@pytest.fixture
async def store(tmp_path):
    s = ScanStore(tmp_path / "test.sqlite")
    await s.open()
    yield s
    await s.close()

async def test_insert_and_query_entries(store):
    await store.insert_entry("scan1", {
        "path": "/var/log/a.txt", "parent": "/var/log", "name": "a.txt",
        "size": 100, "type": "file", "ext": "txt",
        "mode": 33188, "mtime": 1000, "inode": 1,
        "uid": 0, "gid": 0, "nlink": 1, "cached": False
    })
    entries = await store.get_children("scan1", "/var/log", limit=100)
    assert len(entries) == 1
    assert entries[0]["name"] == "a.txt"
    assert entries[0]["size"] == 100

async def test_get_children_respects_limit(store):
    for i in range(10):
        await store.insert_entry("scan1", {
            "path": f"/x/{i}", "parent": "/x", "name": str(i),
            "size": i, "type": "file", "ext": "", "mode": 0, "mtime": 0,
            "inode": 0, "uid": 0, "gid": 0, "nlink": 1, "cached": False
        })
    entries = await store.get_children("scan1", "/x", limit=5)
    assert len(entries) == 5

async def test_get_top_large_files(store):
    for size in [100, 5000, 200, 9999]:
        await store.insert_entry("scan1", {
            "path": f"/f{size}", "parent": "/", "name": f"f{size}",
            "size": size, "type": "file", "ext": "", "mode": 0, "mtime": 0,
            "inode": 0, "uid": 0, "gid": 0, "nlink": 1, "cached": False
        })
    top = await store.get_top_large("scan1", limit=2)
    assert len(top) == 2
    assert top[0]["size"] == 9999
    assert top[1]["size"] == 5000

async def test_delete_entry(store):
    await store.insert_entry("scan1", {
        "path": "/del", "parent": "/", "name": "del",
        "size": 0, "type": "file", "ext": "", "mode": 0, "mtime": 0,
        "inode": 0, "uid": 0, "gid": 0, "nlink": 1, "cached": False
    })
    await store.delete_entry("scan1", "/del")
    entries = await store.get_children("scan1", "/")
    assert all(e["path"] != "/del" for e in entries)
