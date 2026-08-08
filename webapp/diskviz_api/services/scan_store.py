from pathlib import Path
from typing import Optional
import aiosqlite

_SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
  path TEXT PRIMARY KEY, parent TEXT, name TEXT,
  size INTEGER, type TEXT, ext TEXT,
  mode INTEGER, mtime INTEGER, inode INTEGER,
  uid INTEGER, gid INTEGER, nlink INTEGER, cached INTEGER
);
CREATE INDEX IF NOT EXISTS idx_parent ON entries(parent);
CREATE INDEX IF NOT EXISTS idx_size ON entries(size DESC);
CREATE INDEX IF NOT EXISTS idx_ext ON entries(ext);
CREATE TABLE IF NOT EXISTS warnings (path TEXT, code TEXT, msg TEXT, ts INTEGER);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""

_ENTRY_COLS = (
    "path", "parent", "name", "size", "type", "ext",
    "mode", "mtime", "inode", "uid", "gid", "nlink", "cached",
)


class ScanStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._db: Optional[aiosqlite.Connection] = None

    async def open(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(str(self.db_path))
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA synchronous=NORMAL")
        await self._db.executescript(_SCHEMA)
        await self._db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def insert_entry(self, scan_id: str, e: dict) -> None:
        cols = ", ".join(_ENTRY_COLS)
        placeholders = ", ".join("?" for _ in _ENTRY_COLS)
        values = tuple(
            1 if c == "cached" and isinstance(e.get(c), bool) else e.get(c, 0)
            for c in _ENTRY_COLS
        )
        sql = f"INSERT OR REPLACE INTO entries ({cols}) VALUES ({placeholders})"
        await self._db.execute(sql, values)

    async def flush(self) -> None:
        await self._db.commit()

    async def get_children(self, scan_id: str, parent: str, limit: int = 500) -> list:
        sql = (
            "SELECT path, parent, name, size, type, ext, mode, mtime, inode, "
            "uid, gid, nlink, cached FROM entries WHERE parent=? "
            "ORDER BY size DESC LIMIT ?"
        )
        async with self._db.execute(sql, (parent, limit)) as cur:
            rows = await cur.fetchall()
        return [dict(zip(_ENTRY_COLS, r)) for r in rows]

    async def get_top_large(self, scan_id: str, limit: int = 100, min_size: int = 0) -> list:
        sql = (
            "SELECT path, parent, name, size, type, ext, mode, mtime, inode, "
            "uid, gid, nlink, cached FROM entries "
            "WHERE type='file' AND size>=? ORDER BY size DESC LIMIT ?"
        )
        async with self._db.execute(sql, (min_size, limit)) as cur:
            rows = await cur.fetchall()
        return [dict(zip(_ENTRY_COLS, r)) for r in rows]

    async def delete_entry(self, scan_id: str, path: str) -> None:
        await self._db.execute("DELETE FROM entries WHERE path=?", (path,))
        await self._db.commit()

    async def insert_warn(self, scan_id: str, warn: dict) -> None:
        await self._db.execute(
            "INSERT INTO warnings (path, code, msg, ts) VALUES (?, ?, ?, ?)",
            (
                warn.get("path", ""),
                warn.get("code", ""),
                warn.get("msg", ""),
                warn.get("ts", 0),
            ),
        )

    async def get_meta(self, key: str) -> Optional[str]:
        async with self._db.execute(
            "SELECT value FROM meta WHERE key=?", (key,)
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else None

    async def set_meta(self, key: str, value: str) -> None:
        await self._db.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            (key, value),
        )
        await self._db.commit()
