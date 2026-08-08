import os
import time

from diskviz_api.main import cleanup_once


async def test_cleanup_removes_old_scans(tmp_path):
    old = tmp_path / "old.sqlite"
    old.touch()
    old_ts = time.time() - 25 * 3600
    os.utime(old, (old_ts, old_ts))
    deleted = await cleanup_once(scans_dir=tmp_path, ttl_seconds=86400)
    assert not old.exists()
    assert deleted == 1


async def test_cleanup_keeps_recent_scans(tmp_path):
    recent = tmp_path / "recent.sqlite"
    recent.touch()
    await cleanup_once(scans_dir=tmp_path, ttl_seconds=86400)
    assert recent.exists()


async def test_cleanup_ignores_non_sqlite_files(tmp_path):
    old_txt = tmp_path / "old.txt"
    old_txt.touch()
    old_ts = time.time() - 25 * 3600
    os.utime(old_txt, (old_ts, old_ts))
    await cleanup_once(scans_dir=tmp_path, ttl_seconds=86400)
    assert old_txt.exists()


async def test_cleanup_returns_count(tmp_path):
    for name in ["a.sqlite", "b.sqlite"]:
        f = tmp_path / name
        f.touch()
        old_ts = time.time() - 25 * 3600
        os.utime(f, (old_ts, old_ts))
    deleted = await cleanup_once(scans_dir=tmp_path, ttl_seconds=86400)
    assert deleted == 2
