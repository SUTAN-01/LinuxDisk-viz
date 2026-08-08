import pytest
from pathlib import Path
from diskviz_api.services.file_ops import FileOps

def test_safe_path_blocks_root():
    ops = FileOps(root="/var")
    with pytest.raises(Exception, match="refused"):
        ops._assert_safe_path("/")

def test_safe_path_blocks_protected_dirs():
    ops = FileOps(root="/var")
    for p in ["/etc", "/etc/passwd", "/proc/sys", "/usr/bin", "/boot/grub",
              "/sys/kernel", "/dev/null", "/bin/sh", "/lib/x", "/sbin/y", "/lib64/z"]:
        with pytest.raises(Exception, match="protected"):
            ops._assert_safe_path(p)

def test_safe_path_blocks_traversal_outside_root():
    ops = FileOps(root="/var/log")
    with pytest.raises(Exception, match="outside scan root"):
        ops._assert_safe_path("/etc/passwd")
    # Root-internal paths are allowed
    ops._assert_safe_path("/var/log/x")
    ops._assert_safe_path("/var/log/nginx/access.log")

def test_delete_permanent_removes_file(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("hello")
    ops = FileOps(root=str(tmp_path))
    ops.delete_permanent(str(f))
    assert not f.exists()

def test_delete_trash_uses_send2trash(tmp_path, monkeypatch):
    f = tmp_path / "y.txt"
    f.write_text("y")
    ops = FileOps(root=str(tmp_path))
    called = []
    monkeypatch.setattr("diskviz_api.services.file_ops.send2trash",
                        lambda p: called.append(p))
    ops.delete_trash(str(f))
    assert called

def test_safe_path_resolves_symlink_outside_root(tmp_path):
    (tmp_path / "outside").write_text("secret")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    link = subdir / "link"
    try:
        link.symlink_to(tmp_path / "outside")
    except OSError as e:
        # Windows requires admin privileges to create symlinks (WinError 1314)
        pytest.skip(f"cannot create symlink on this platform: {e}")
    ops = FileOps(root=str(subdir))
    # symlink resolves outside root — should be blocked
    with pytest.raises(Exception):
        ops._assert_safe_path(str(link))
    # but the subdir itself is fine
    ops._assert_safe_path(str(subdir / "normal.txt"))
