import json
import time
import asyncio
from pathlib import Path
from typing import Optional


class AuditLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def write(self, action: str, user: str, path: str,
                    options: dict = {}, success: bool = True,
                    err: Optional[str] = None):
        record = {
            "ts": time.time(),
            "action": action,
            "user": user,
            "path": path,
            "options": options,
            "success": success,
        }
        if err:
            record["err"] = err
        line = json.dumps(record, ensure_ascii=False)
        async with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
