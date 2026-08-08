import asyncio
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from diskviz_api.main import app
from diskviz_api.services.dup_detector import DupDetector
from diskviz_api.services.scan_store import ScanStore
from diskviz_api.services.scanner_runner import ScanManager, RunningScan

mock_scanner = str(Path(__file__).parent.parent / "fixtures" / "mock_scanner.py")
READ_HEADERS = {"Authorization": "Bearer dev-read"}


def _entry(path: str, size: int, name: str = "", parent: str = "") -> dict:
    return {
        "path": path,
        "parent": parent or str(Path(path).parent),
        "name": name or Path(path).name,
        "size": size,
        "type": "file",
        "ext": Path(path).suffix,
        "mode": 33188,
        "mtime": 1000,
        "inode": 0,
        "uid": 0,
        "gid": 0,
        "nlink": 1,
        "cached": 0,
    }


@pytest.fixture
async def managers(tmp_path):
    """Open a real ScanStore on the test loop and register a finished scan."""
    app.state.scan_manager = ScanManager(
        scanner_binary="D:\\anaconda3\\python.exe",
        scanner_args=[mock_scanner],
        cache_path=str(tmp_path / "c.sqlite"),
        scans_dir=tmp_path,
    )
    app.state.dup_detector = DupDetector()
    store = ScanStore(tmp_path / "s1.sqlite")
    await store.open()
    app.state.scan_manager._scans["s1"] = RunningScan(
        scan_id="s1", root=str(tmp_path), proc=None, started_at=0,
        store=store, finished=True,
    )
    yield store
    await store.close()
    app.state.scan_manager._scans.clear()


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_top_large_returns_entries(tmp_path, managers):
    store = managers
    await store.insert_entry("s1", _entry(str(tmp_path / "big1.bin"), 1000))
    await store.insert_entry("s1", _entry(str(tmp_path / "big2.bin"), 500))
    await store.flush()
    async with await _client() as client:
        r = await client.get("/reports/top-large/s1", params={"limit": 10},
                             headers=READ_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2
    assert body["entries"][0]["size"] == 1000
    assert body["entries"][1]["size"] == 500


async def test_top_large_404_for_unknown_scan(managers):
    async with await _client() as client:
        r = await client.get("/reports/top-large/nope", headers=READ_HEADERS)
    assert r.status_code == 404


async def test_top_large_respects_min_size(tmp_path, managers):
    store = managers
    await store.insert_entry("s1", _entry(str(tmp_path / "big1.bin"), 1000))
    await store.insert_entry("s1", _entry(str(tmp_path / "big2.bin"), 500))
    await store.flush()
    async with await _client() as client:
        r = await client.get("/reports/top-large/s1",
                             params={"limit": 10, "min_size": 800},
                             headers=READ_HEADERS)
    assert r.status_code == 200
    assert r.json()["count"] == 1
    assert r.json()["entries"][0]["size"] == 1000


async def test_top_large_rejects_missing_token(tmp_path, managers):
    store = managers
    await store.insert_entry("s1", _entry(str(tmp_path / "big1.bin"), 1000))
    await store.flush()
    async with await _client() as client:
        r = await client.get("/reports/top-large/s1")
    assert r.status_code == 401


async def test_export_csv(tmp_path, managers):
    store = managers
    await store.insert_entry("s1", _entry(str(tmp_path / "big1.bin"), 1000))
    await store.insert_entry("s1", _entry(str(tmp_path / "big2.bin"), 500))
    await store.flush()
    async with await _client() as client:
        r = await client.get("/reports/export/s1", params={"format": "csv"},
                             headers=READ_HEADERS)
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "attachment" in r.headers["content-disposition"]
    text = r.text
    assert "path" in text  # header
    assert "big1.bin" in text
    assert "big2.bin" in text


async def test_export_json(tmp_path, managers):
    store = managers
    await store.insert_entry("s1", _entry(str(tmp_path / "big1.bin"), 1000))
    await store.flush()
    async with await _client() as client:
        r = await client.get("/reports/export/s1", params={"format": "json"},
                             headers=READ_HEADERS)
    assert r.status_code == 200
    assert "application/json" in r.headers["content-type"]
    body = r.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["name"] == "big1.bin"


async def test_export_404_for_unknown_scan(managers):
    async with await _client() as client:
        r = await client.get("/reports/export/nope", headers=READ_HEADERS)
    assert r.status_code == 404


async def test_dup_detection_job(tmp_path, managers):
    store = managers
    # Real duplicate files on disk (same content + size)
    dup1 = tmp_path / "dup1.bin"
    dup2 = tmp_path / "dup2.bin"
    dup1.write_bytes(b"same content")
    dup2.write_bytes(b"same content")
    # A unique file (different content + size)
    uniq = tmp_path / "uniq.bin"
    uniq.write_bytes(b"unique")
    await store.insert_entry("s1", _entry(str(dup1), 12))
    await store.insert_entry("s1", _entry(str(dup2), 12))
    await store.insert_entry("s1", _entry(str(uniq), 6))
    await store.flush()

    async with await _client() as client:
        r = await client.post("/reports/duplicates/s1", headers=READ_HEADERS)
        assert r.status_code == 200
        job_id = r.json()["job_id"]
        assert r.json()["status"] == "running"
        assert r.json()["paths_count"] == 3

        st = None
        for _ in range(100):
            r = await client.get(f"/reports/duplicates/s1/{job_id}",
                                 headers=READ_HEADERS)
            st = r.json()
            if st["status"] == "done":
                break
            await asyncio.sleep(0.02)

    assert st is not None
    assert st["status"] == "done"
    assert st["groups"] is not None
    assert len(st["groups"]) == 1
    assert st["groups"][0]["count"] == 2
    assert len(st["groups"][0]["paths"]) == 2
    assert st["groups"][0]["size"] == 12
    assert st["groups"][0]["wasted"] == 12


async def test_dup_status_404_for_unknown_job(tmp_path, managers):
    async with await _client() as client:
        r = await client.get("/reports/duplicates/s1/no-such-job",
                             headers=READ_HEADERS)
    assert r.status_code == 404


async def test_dup_status_404_for_unknown_scan(managers):
    async with await _client() as client:
        r = await client.get("/reports/duplicates/nope/somejob",
                             headers=READ_HEADERS)
    assert r.status_code == 404
