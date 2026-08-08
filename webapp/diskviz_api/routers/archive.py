from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..auth import require_token, verify_confirm_token
from ..services.file_ops import FileOps

router = APIRouter()


class PackReq(BaseModel):
    paths: List[str]
    format: str = "tar.gz"  # "tar.gz" | "zip"
    confirm_token: str


def _get_fileops() -> FileOps:
    from ..main import app
    return FileOps.from_app(app)


def _get_manager():
    from ..main import app
    return app.state.archive_manager


@router.post("/archive/pack")
async def pack(req: PackReq, user=Depends(require_token(True))):
    if not verify_confirm_token(req.confirm_token):
        raise HTTPException(403, "confirm_token invalid")
    if req.format not in ("tar.gz", "zip"):
        raise HTTPException(400, "format must be tar.gz or zip")
    ops = _get_fileops()
    for p in req.paths:
        ops._assert_safe_path(p)
    mgr = _get_manager()
    job_id = mgr.pack(req.paths, req.format)
    return {"job_id": job_id, "status": "running"}


@router.get("/archive/{job_id}")
async def status(job_id: str, user=Depends(require_token(False))):
    mgr = _get_manager()
    try:
        return mgr.get_status(job_id)
    except KeyError:
        raise HTTPException(404, "job not found")


@router.get("/archive/{job_id}/download")
async def download(job_id: str, user=Depends(require_token(False))):
    mgr = _get_manager()
    try:
        st = mgr.get_status(job_id)
    except KeyError:
        raise HTTPException(404, "job not found")
    if st["status"] != "done":
        raise HTTPException(409, f"job not done: {st['status']}")
    out = Path(st["out_path"])
    if not out.exists():
        raise HTTPException(404, "archive file missing")
    media = "application/gzip" if st["format"] == "tar.gz" else "application/zip"
    return FileResponse(str(out), media_type=media, filename=out.name)
