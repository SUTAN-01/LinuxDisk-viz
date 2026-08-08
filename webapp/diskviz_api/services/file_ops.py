from pathlib import Path
from fastapi import HTTPException
from send2trash import send2trash
import shutil


class FileOps:
    BLOCKED_PREFIXES = ["/proc", "/sys", "/dev", "/run", "/boot",
                        "/etc", "/usr", "/bin", "/sbin", "/lib", "/lib64"]

    def __init__(self, root: str):
        self.root = root
        self.root_resolved = Path(root).resolve(strict=False)

    def _assert_safe_path(self, p: str):
        real = Path(p).resolve(strict=False)
        # Block root / (also Windows drive root like C:\)
        if str(real) == "/" or str(real) == str(real.anchor):
            raise HTTPException(400, "refused to operate on root")

        # Normalize original path for cross-platform prefix matching. On Linux
        # this is a no-op; on Windows it lets Unix-style test paths ("/etc")
        # match the blocked prefixes.
        s = str(p).replace("\\", "/")

        # Check if path is in a protected system directory
        protected_prefix = None
        for b in self.BLOCKED_PREFIXES:
            if s == b or s.startswith(b + "/"):
                protected_prefix = b
                break

        # Check if resolved path is outside scan root
        try:
            real.relative_to(self.root_resolved)
            outside_root = False
        except ValueError:
            outside_root = True

        if protected_prefix and outside_root:
            raise HTTPException(
                400,
                f"refused to operate on protected path outside scan root: {p}",
            )
        if protected_prefix:
            raise HTTPException(400, f"refused to operate on protected path: {p}")
        if outside_root:
            raise HTTPException(400, f"path outside scan root: {p}")

    def delete_permanent(self, path: str):
        self._assert_safe_path(path)
        p = Path(path)
        if p.is_file() or p.is_symlink():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)

    def delete_trash(self, path: str):
        self._assert_safe_path(path)
        send2trash(path)

    def move(self, src: str, dst_dir: str):
        self._assert_safe_path(src)
        self._assert_safe_path(dst_dir)
        Path(dst_dir).mkdir(parents=True, exist_ok=True)
        shutil.move(src, Path(dst_dir) / Path(src).name)

    def rename(self, path: str, new_name: str):
        self._assert_safe_path(path)
        if "/" in new_name or "\\" in new_name or ".." in new_name or "\0" in new_name:
            raise HTTPException(400, "invalid new_name")
        p = Path(path)
        p.rename(p.parent / new_name)

    def mkdir(self, path: str):
        self._assert_safe_path(path)
        Path(path).mkdir(parents=True, exist_ok=True)
