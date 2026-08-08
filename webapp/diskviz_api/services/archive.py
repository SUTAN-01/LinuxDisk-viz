import asyncio
import tarfile
import zipfile
import uuid
import time
from pathlib import Path
from typing import Optional


class ArchiveManager:
    """Manages async archive (tar.gz/zip) packing jobs."""

    def __init__(self, scans_dir: Path):
        self.scans_dir = Path(scans_dir)
        self.archives_dir = self.scans_dir / "archives"
        self.archives_dir.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, dict] = {}  # job_id -> status dict

    def pack(self, paths: list[str], fmt: str = "tar.gz") -> str:
        """Create an archive job and return its job_id.

        Packing runs in a background asyncio task; poll get_status() for
        completion.
        """
        job_id = f"arc-{uuid.uuid4().hex[:12]}"
        out_path = self.archives_dir / f"{job_id}.{fmt}"
        self._jobs[job_id] = {
            "job_id": job_id,
            "status": "running",
            "format": fmt,
            "out_path": str(out_path),
            "paths": list(paths),
            "started_at": time.time(),
            "finished_at": None,
            "error": None,
        }
        asyncio.create_task(self._run_pack(job_id, paths, fmt, out_path))
        return job_id

    async def _run_pack(self, job_id: str, paths: list[str], fmt: str,
                        out_path: Path):
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self._do_pack_sync,
                                       paths, fmt, out_path)
            self._jobs[job_id]["status"] = "done"
            self._jobs[job_id]["finished_at"] = time.time()
        except Exception as e:
            self._jobs[job_id]["status"] = "error"
            self._jobs[job_id]["error"] = str(e)

    def _do_pack_sync(self, paths: list[str], fmt: str, out_path: Path):
        if fmt == "tar.gz":
            with tarfile.open(out_path, "w:gz") as tar:
                for p in paths:
                    tar.add(p, arcname=Path(p).name)
        elif fmt == "zip":
            with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for p in paths:
                    zf.write(p, arcname=Path(p).name)
        else:
            raise ValueError(f"unsupported format: {fmt}")

    def get_status(self, job_id: str) -> dict:
        if job_id not in self._jobs:
            raise KeyError(job_id)
        return self._jobs[job_id]
