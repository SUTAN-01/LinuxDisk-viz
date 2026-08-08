from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from ..auth import require_token, verify_confirm_token
from ..services.file_ops import FileOps
from ..services.audit_log import AuditLog
from ..config import settings

router = APIRouter()

_audit = AuditLog(settings.audit_log)


class DeleteReq(BaseModel):
    paths: List[str]
    mode: str  # "trash" | "permanent"
    confirm_token: str


class MoveReq(BaseModel):
    src_paths: List[str]
    dst_dir: str
    confirm_token: str


class RenameReq(BaseModel):
    path: str
    new_name: str
    confirm_token: str


class MkdirReq(BaseModel):
    path: str
    confirm_token: str


def _get_fileops() -> FileOps:
    from ..main import app
    return FileOps.from_app(app)


@router.post("/ops/delete")
async def delete(req: DeleteReq, user=Depends(require_token(True))):
    if not verify_confirm_token(req.confirm_token):
        raise HTTPException(403, "confirm_token invalid")
    ops = _get_fileops()
    user_id = user.get("token", "anon")[:8]
    results = []
    for p in req.paths:
        try:
            if req.mode == "trash":
                ops.delete_trash(p)
            else:
                ops.delete_permanent(p)
            try:
                await _audit.write("delete", user_id, p, {"mode": req.mode}, True)
            except Exception:
                pass
            results.append({"path": p, "ok": True})
        except HTTPException as e:
            try:
                await _audit.write("delete", user_id, p, {"mode": req.mode}, False, str(e.detail))
            except Exception:
                pass
            results.append({"path": p, "ok": False, "err": e.detail})
        except Exception as e:
            try:
                await _audit.write("delete", user_id, p, {"mode": req.mode}, False, str(e))
            except Exception:
                pass
            results.append({"path": p, "ok": False, "err": str(e)})
    return {"results": results}


@router.post("/ops/move")
async def move(req: MoveReq, user=Depends(require_token(True))):
    if not verify_confirm_token(req.confirm_token):
        raise HTTPException(403, "confirm_token invalid")
    ops = _get_fileops()
    user_id = user.get("token", "anon")[:8]
    results = []
    for src in req.src_paths:
        try:
            ops.move(src, req.dst_dir)
            try:
                await _audit.write("move", user_id, src, {"dst_dir": req.dst_dir}, True)
            except Exception:
                pass
            results.append({"path": src, "ok": True})
        except Exception as e:
            try:
                await _audit.write("move", user_id, src, {"dst_dir": req.dst_dir}, False, str(e))
            except Exception:
                pass
            results.append({"path": src, "ok": False, "err": str(e)})
    return {"results": results}


@router.post("/ops/rename")
async def rename(req: RenameReq, user=Depends(require_token(True))):
    if not verify_confirm_token(req.confirm_token):
        raise HTTPException(403, "confirm_token invalid")
    ops = _get_fileops()
    user_id = user.get("token", "anon")[:8]
    try:
        ops.rename(req.path, req.new_name)
        try:
            await _audit.write("rename", user_id, req.path, {"new_name": req.new_name}, True)
        except Exception:
            pass
        return {"ok": True}
    except Exception as e:
        try:
            await _audit.write("rename", user_id, req.path, {"new_name": req.new_name}, False, str(e))
        except Exception:
            pass
        return {"ok": False, "err": str(e)}


@router.post("/ops/mkdir")
async def mkdir(req: MkdirReq, user=Depends(require_token(True))):
    if not verify_confirm_token(req.confirm_token):
        raise HTTPException(403, "confirm_token invalid")
    ops = _get_fileops()
    user_id = user.get("token", "anon")[:8]
    try:
        ops.mkdir(req.path)
        try:
            await _audit.write("mkdir", user_id, req.path, {}, True)
        except Exception:
            pass
        return {"ok": True}
    except Exception as e:
        try:
            await _audit.write("mkdir", user_id, req.path, {}, False, str(e))
        except Exception:
            pass
        return {"ok": False, "err": str(e)}
