from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from ..auth import require_token, verify_confirm_token
from ..services.file_ops import FileOps

router = APIRouter()


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
    mgr = app.state.scan_manager
    root = "/"
    for rs in mgr._scans.values():
        if rs.finished:
            root = rs.root
            break
    return FileOps(root=root)


@router.post("/ops/delete")
async def delete(req: DeleteReq, user=Depends(require_token(True))):
    if not verify_confirm_token(req.confirm_token):
        raise HTTPException(403, "confirm_token invalid")
    ops = _get_fileops()
    results = []
    for p in req.paths:
        try:
            if req.mode == "trash":
                ops.delete_trash(p)
            else:
                ops.delete_permanent(p)
            results.append({"path": p, "ok": True})
        except HTTPException as e:
            results.append({"path": p, "ok": False, "err": e.detail})
        except Exception as e:
            results.append({"path": p, "ok": False, "err": str(e)})
    return {"results": results}


@router.post("/ops/move")
async def move(req: MoveReq, user=Depends(require_token(True))):
    if not verify_confirm_token(req.confirm_token):
        raise HTTPException(403, "confirm_token invalid")
    ops = _get_fileops()
    results = []
    for src in req.src_paths:
        try:
            ops.move(src, req.dst_dir)
            results.append({"path": src, "ok": True})
        except Exception as e:
            results.append({"path": src, "ok": False, "err": str(e)})
    return {"results": results}


@router.post("/ops/rename")
async def rename(req: RenameReq, user=Depends(require_token(True))):
    if not verify_confirm_token(req.confirm_token):
        raise HTTPException(403, "confirm_token invalid")
    ops = _get_fileops()
    try:
        ops.rename(req.path, req.new_name)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "err": str(e)}


@router.post("/ops/mkdir")
async def mkdir(req: MkdirReq, user=Depends(require_token(True))):
    if not verify_confirm_token(req.confirm_token):
        raise HTTPException(403, "confirm_token invalid")
    ops = _get_fileops()
    try:
        ops.mkdir(req.path)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "err": str(e)}
