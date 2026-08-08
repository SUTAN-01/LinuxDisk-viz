import json
import pytest
from pathlib import Path
from diskviz_api.services.audit_log import AuditLog

async def test_write_creates_jsonl_line(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    await log.write("delete", "user1", "/var/log/x", {"mode": "permanent"}, success=True)
    await log.write("move", "user2", "/old", {"dst": "/new"}, success=False, err="EACCES")
    lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    e1 = json.loads(lines[0])
    assert e1["action"] == "delete"
    assert e1["user"] == "user1"
    assert e1["success"] is True
    e2 = json.loads(lines[1])
    assert e2["success"] is False
    assert e2["err"] == "EACCES"

async def test_audit_includes_timestamp(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    await log.write("mkdir", "u", "/x", {}, True)
    line = (tmp_path / "audit.jsonl").read_text(encoding="utf-8")
    e = json.loads(line)
    assert "ts" in e
    assert isinstance(e["ts"], (int, float))
