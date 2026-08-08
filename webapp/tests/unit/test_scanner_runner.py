import pytest
import asyncio
from pathlib import Path
from diskviz_api.services.scanner_runner import ScanManager

@pytest.fixture
def mock_scanner_path():
    return str(Path(__file__).parent.parent / "fixtures" / "mock_scanner.py")

async def test_start_returns_scan_id(mock_scanner_path, tmp_path):
    mgr = ScanManager(scanner_binary="D:\\anaconda3\\python.exe",
                      scanner_args=[mock_scanner_path],
                      cache_path=str(tmp_path / "c.sqlite"),
                      scans_dir=tmp_path)
    scan_id = await mgr.start("/tmp", workers=2)
    assert scan_id
    await asyncio.sleep(1)
    rs = mgr._scans[scan_id]
    assert rs.finished
    assert rs.result["total_entries"] == 3

async def test_subscriber_receives_done(mock_scanner_path, tmp_path):
    mgr = ScanManager(scanner_binary="D:\\anaconda3\\python.exe",
                      scanner_args=[mock_scanner_path],
                      cache_path=str(tmp_path / "c.sqlite"),
                      scans_dir=tmp_path)
    scan_id = await mgr.start("/tmp", workers=2)
    frames = []
    async for frame in mgr.subscribe(scan_id):
        frames.append(frame)
        if frame.get("type") == "done":
            break
    assert any(f.get("type") == "done" for f in frames)
