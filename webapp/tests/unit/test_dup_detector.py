import asyncio

import pytest

from diskviz_api.services.dup_detector import DupDetector


async def test_detect_finds_duplicates_by_size(tmp_path):
    (tmp_path / "a").write_bytes(b"hello")
    (tmp_path / "b").write_bytes(b"hello")
    (tmp_path / "c").write_bytes(b"different")
    det = DupDetector()
    groups = await det.detect(
        [str(tmp_path / "a"), str(tmp_path / "b"), str(tmp_path / "c")],
        min_size=0,
    )
    assert len(groups) == 1
    assert len(groups[0]["paths"]) == 2
    assert groups[0]["size"] == 5
    assert groups[0]["count"] == 2
    assert groups[0]["wasted"] == 5


async def test_detect_handles_empty_file_duplicates(tmp_path):
    (tmp_path / "a").write_bytes(b"")
    (tmp_path / "b").write_bytes(b"")
    (tmp_path / "c").write_bytes(b"")
    det = DupDetector()
    groups = await det.detect(
        [str(tmp_path / "a"), str(tmp_path / "b"), str(tmp_path / "c")],
        min_size=0,
    )
    assert len(groups) == 1
    assert len(groups[0]["paths"]) == 3
    assert groups[0]["size"] == 0
    assert groups[0]["count"] == 3
    assert groups[0]["wasted"] == 0


async def test_detect_respects_min_size(tmp_path):
    (tmp_path / "a").write_bytes(b"hi")  # size 2
    (tmp_path / "b").write_bytes(b"hi")  # size 2
    det = DupDetector()
    groups = await det.detect(
        [str(tmp_path / "a"), str(tmp_path / "b")], min_size=10
    )
    assert groups == []


async def test_detect_handles_missing_file(tmp_path):
    (tmp_path / "a").write_bytes(b"hello")
    (tmp_path / "b").write_bytes(b"hello")
    det = DupDetector()
    groups = await det.detect(
        [str(tmp_path / "a"), str(tmp_path / "b"), str(tmp_path / "missing")],
        min_size=0,
    )
    assert len(groups) == 1
    assert len(groups[0]["paths"]) == 2


async def test_start_job_returns_done_status(tmp_path):
    (tmp_path / "a").write_bytes(b"hello")
    (tmp_path / "b").write_bytes(b"hello")
    det = DupDetector()
    job_id = det.start_job([str(tmp_path / "a"), str(tmp_path / "b")], min_size=0)
    st = None
    for _ in range(50):
        st = det.get_status(job_id)
        if st["status"] == "done":
            break
        await asyncio.sleep(0.02)
    assert st is not None
    assert st["status"] == "done"
    assert st["groups"] is not None
    assert len(st["groups"]) == 1
    assert len(st["groups"][0]["paths"]) == 2
    assert st["finished_at"] is not None


async def test_get_status_unknown_job_raises():
    det = DupDetector()
    with pytest.raises(KeyError):
        det.get_status("does-not-exist")


async def test_detect_same_prefix_different_suffix_not_grouped(tmp_path):
    # Two files of equal size (>4KB) sharing the first 4KB but differing after.
    prefix = b"A" * 4096
    (tmp_path / "x.bin").write_bytes(prefix + b"B" * 4096)
    (tmp_path / "y.bin").write_bytes(prefix + b"C" * 4096)
    det = DupDetector()
    groups = await det.detect(
        [str(tmp_path / "x.bin"), str(tmp_path / "y.bin")], min_size=0
    )
    assert groups == []
