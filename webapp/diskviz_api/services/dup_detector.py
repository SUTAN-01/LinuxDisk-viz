import asyncio
import hashlib
import os
import time
import uuid

_PARTIAL_SIZE = 4096  # 4KB partial hash
_READ_BUF = 65536     # 64KB full hash buffer


class DupDetector:
    """Detects duplicate files using a size -> partial-hash -> full-hash strategy.

    Pure-Python implementation backed by hashlib (sha256) so it works without
    the C++ scanner binary.
    """

    def __init__(self):
        self._jobs: dict[str, dict] = {}  # job_id -> status

    async def detect(self, paths: list[str], min_size: int = 0) -> list[dict]:
        """Detect duplicate files among paths. Returns list of dup groups.

        Each group: {"size": int, "count": int, "paths": [...], "wasted": int}
        """
        # Group by size first; only sizes with 2+ files are candidates.
        sized: dict[int, list[str]] = {}
        for p in paths:
            try:
                st = os.stat(p)
            except OSError:
                continue
            if st.st_size < min_size:
                continue
            sized.setdefault(st.st_size, []).append(p)

        groups: list[dict] = []
        for size, ps in sized.items():
            if len(ps) < 2:
                continue
            # Partial hash (first 4KB)
            partials: dict[str, list[str]] = {}
            for p in ps:
                h = await self._partial_hash(p)
                partials.setdefault(h, []).append(p)
            for ph, phs in partials.items():
                if len(phs) < 2:
                    continue
                # Full hash
                fulls: dict[str, list[str]] = {}
                for p in phs:
                    h = await self._full_hash(p)
                    fulls.setdefault(h, []).append(p)
                for fh, fps in fulls.items():
                    if len(fps) < 2:
                        continue
                    groups.append({
                        "size": size,
                        "count": len(fps),
                        "paths": fps,
                        "wasted": size * (len(fps) - 1),
                    })
        return groups

    async def _partial_hash(self, path: str) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._partial_hash_sync, path)

    def _partial_hash_sync(self, path: str) -> str:
        h = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                h.update(f.read(_PARTIAL_SIZE))
        except OSError:
            return f"err-{uuid.uuid4().hex}"  # unique, won't match
        return h.hexdigest()

    async def _full_hash(self, path: str) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._full_hash_sync, path)

    def _full_hash_sync(self, path: str) -> str:
        h = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                while True:
                    buf = f.read(_READ_BUF)
                    if not buf:
                        break
                    h.update(buf)
        except OSError:
            return f"err-{uuid.uuid4().hex}"
        return h.hexdigest()

    def start_job(self, paths: list[str], min_size: int = 0) -> str:
        """Start background detection job. Returns job_id."""
        job_id = f"dup-{uuid.uuid4().hex[:12]}"
        self._jobs[job_id] = {
            "job_id": job_id,
            "status": "running",
            "paths_count": len(paths),
            "min_size": min_size,
            "started_at": time.time(),
            "finished_at": None,
            "groups": None,
            "error": None,
        }
        asyncio.create_task(self._run_job(job_id, paths, min_size))
        return job_id

    async def _run_job(self, job_id: str, paths: list[str], min_size: int):
        try:
            groups = await self.detect(paths, min_size)
            self._jobs[job_id]["groups"] = groups
            self._jobs[job_id]["status"] = "done"
            self._jobs[job_id]["finished_at"] = time.time()
        except Exception as e:
            self._jobs[job_id]["status"] = "error"
            self._jobs[job_id]["error"] = str(e)

    def get_status(self, job_id: str) -> dict:
        if job_id not in self._jobs:
            raise KeyError(job_id)
        return dict(self._jobs[job_id])  # shallow copy
