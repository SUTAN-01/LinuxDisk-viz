import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator, Optional

from .scan_store import ScanStore
from ..config import settings

@dataclass
class RunningScan:
    scan_id: str
    root: str
    proc: asyncio.subprocess.Process
    started_at: float
    subscribers: list = field(default_factory=list)
    last_progress: Optional[dict] = None
    finished: bool = False
    result: Optional[dict] = None
    store: Optional[ScanStore] = None

class ScanManager:
    def __init__(self, scanner_binary: str = None, scanner_args: list = None,
                 cache_path: str = None, scans_dir: Path = None):
        self._scans: dict[str, RunningScan] = {}
        self._lock = asyncio.Lock()
        self._scanner_binary = scanner_binary or str(settings.scanner_binary)
        self._scanner_args = scanner_args or []
        self._cache_path = cache_path or str(settings.cache_path)
        self._scans_dir = Path(scans_dir) if scans_dir else settings.scans_dir

    async def start(self, root: str, workers: int = 0) -> str:
        scan_id = uuid.uuid4().hex
        store_path = self._scans_dir / f"{scan_id}.sqlite"
        store = ScanStore(store_path)
        await store.open()
        await store.set_meta("root", root)
        await store.set_meta("started_at", str(int(time.time())))

        cmd = [self._scanner_binary] + self._scanner_args + [
            "--root", root, "--ndjson",
            "--cache", self._cache_path, "--progress-every", "1000"
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        rs = RunningScan(scan_id=scan_id, root=root, proc=proc,
                         started_at=time.time(), store=store)
        async with self._lock:
            self._scans[scan_id] = rs
        asyncio.create_task(self._pump_stdout(rs))
        asyncio.create_task(self._pump_stderr(rs))
        return scan_id

    async def _pump_stdout(self, rs: RunningScan):
        async for line in rs.proc.stdout:
            line = line.decode().strip()
            if not line:
                continue
            try:
                frame = json.loads(line)
            except json.JSONDecodeError:
                continue
            await self._handle_frame(rs, frame)

    async def _pump_stderr(self, rs: RunningScan):
        async for line in rs.proc.stderr:
            pass  # log later

    async def _handle_frame(self, rs: RunningScan, frame: dict):
        t = frame.get("type")
        if t == "entry":
            await rs.store.insert_entry(rs.scan_id, {
                "path": frame["path"],
                "parent": str(Path(frame["path"]).parent) if frame["path"] != "/" else "",
                "name": Path(frame["path"]).name,
                "size": frame["size"], "type": frame.get("kind", "file"), "ext": frame.get("ext", ""),
                "mode": frame.get("mode", 0), "mtime": frame.get("mtime", 0),
                "inode": frame.get("inode", 0), "uid": frame.get("uid", 0),
                "gid": frame.get("gid", 0), "nlink": frame.get("nlink", 0),
                "cached": frame.get("cached", False)
            })
        elif t == "progress":
            rs.last_progress = frame
            await self._broadcast(rs, frame)
        elif t == "warn":
            await rs.store.insert_warn(rs.scan_id, frame)
            await self._broadcast(rs, frame)
        elif t == "scan.end":
            await rs.store.flush()
            rs.finished = True
            rs.result = frame
            await self._broadcast(rs, {**frame, "type": "done"})

    async def _broadcast(self, rs: RunningScan, frame: dict):
        for q in rs.subscribers:
            try:
                q.put_nowait(frame)
            except asyncio.QueueFull:
                pass

    async def subscribe(self, scan_id: str) -> AsyncIterator[dict]:
        async with self._lock:
            rs = self._scans[scan_id]
            q: asyncio.Queue = asyncio.Queue(maxsize=1024)
            rs.subscribers.append(q)
            already_finished = rs.finished
            last_progress = rs.last_progress
            result = rs.result
        try:
            if last_progress:
                yield last_progress
            if already_finished and result is not None:
                yield {**result, "type": "done"}
                return
            while True:
                frame = await q.get()
                yield frame
                if frame.get("type") == "done":
                    break
        finally:
            async with self._lock:
                if q in rs.subscribers:
                    rs.subscribers.remove(q)

    async def cancel_all(self):
        for rs in self._scans.values():
            if rs.proc and rs.proc.returncode is None:
                rs.proc.terminate()
                try:
                    await asyncio.wait_for(rs.proc.wait(), timeout=5)
                except asyncio.TimeoutError:
                    rs.proc.kill()
