import os
import uuid
import time
from pathlib import Path


class UploadManager:
    """Manages tus-like chunked uploads.

    Flow: create(target_dir, length) -> append(id, offset, data)*
    -> complete(id, filename) which moves the tmp file into target_dir.
    """

    def __init__(self, scans_dir: Path):
        self.scans_dir = Path(scans_dir)
        self.uploads_dir = self.scans_dir / "uploads"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, dict] = {}  # upload_id -> session info

    def create(self, target_dir: str, length: int) -> str:
        """Create an upload session. Returns upload_id."""
        if length < 0:
            raise ValueError("length must be >= 0")
        upload_id = f"up-{uuid.uuid4().hex[:12]}"
        tmp_path = self.uploads_dir / f"{upload_id}.tmp"
        # Create empty tmp file
        tmp_path.touch()
        self._sessions[upload_id] = {
            "upload_id": upload_id,
            "target_dir": target_dir,
            "length": length,
            "tmp_path": str(tmp_path),
            "offset": 0,
            "created_at": time.time(),
            "completed": False,
        }
        return upload_id

    def append(self, upload_id: str, offset: int, data: bytes) -> int:
        """Append chunk at offset. Returns new offset."""
        if upload_id not in self._sessions:
            raise KeyError(upload_id)
        sess = self._sessions[upload_id]
        if sess["completed"]:
            raise ValueError("upload already completed")
        if offset != sess["offset"]:
            raise ValueError(
                f"offset mismatch: expected {sess['offset']}, got {offset}"
            )
        tmp_path = Path(sess["tmp_path"])
        with open(tmp_path, "ab") as f:
            f.write(data)
        sess["offset"] += len(data)
        if sess["offset"] > sess["length"]:
            raise ValueError(
                f"uploaded bytes exceed declared length {sess['length']}"
            )
        return sess["offset"]

    def complete(self, upload_id: str, filename: str) -> str:
        """Finalize upload: sanitize filename, move tmp to target_dir/filename.

        Returns final path.
        """
        if upload_id not in self._sessions:
            raise KeyError(upload_id)
        sess = self._sessions[upload_id]
        if sess["completed"]:
            raise ValueError("upload already completed")
        safe_name = self._sanitize_filename(filename)
        target_dir = Path(sess["target_dir"])
        target_dir.mkdir(parents=True, exist_ok=True)
        final_path = target_dir / safe_name
        tmp_path = Path(sess["tmp_path"])
        os.replace(tmp_path, final_path)
        sess["completed"] = True
        sess["final_path"] = str(final_path)
        return str(final_path)

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Reject path separators, .. traversal, null bytes; basename only."""
        if not filename:
            raise ValueError("filename required")
        if "/" in filename or "\\" in filename or ".." in filename or "\0" in filename:
            raise ValueError("invalid filename")
        # Take basename as extra safety
        name = filename.replace("\\", "/").split("/")[-1]
        if not name or name in (".", ".."):
            raise ValueError("invalid filename")
        return name

    def get_status(self, upload_id: str) -> dict:
        if upload_id not in self._sessions:
            raise KeyError(upload_id)
        return self._sessions[upload_id]
