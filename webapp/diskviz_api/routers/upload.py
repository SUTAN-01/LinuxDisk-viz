from fastapi import APIRouter, Depends, HTTPException, Request, Query

from ..auth import require_token
from ..services.file_ops import FileOps
from ..services.upload import UploadConflictError

router = APIRouter()


def _get_manager(request: Request):
    return request.app.state.upload_manager


@router.post("/upload")
async def create_upload(
    request: Request,
    path: str = Query(..., description="target directory"),
    user=Depends(require_token(True)),
):
    """Create upload session. Reads Upload-Length header (tus-like)."""
    length_hdr = request.headers.get("Upload-Length")
    if length_hdr is None:
        raise HTTPException(400, "missing Upload-Length header")
    try:
        length = int(length_hdr)
    except ValueError:
        raise HTTPException(400, "Upload-Length must be integer")
    if length < 0:
        raise HTTPException(400, "Upload-Length must be >= 0")
    # Validate target dir is safe
    FileOps.from_app(request.app)._assert_safe_path(path)
    mgr = _get_manager(request)
    try:
        upload_id = mgr.create(path, length)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"upload_id": upload_id, "length": length}


@router.patch("/upload/{upload_id}")
async def append_upload(
    upload_id: str,
    request: Request,
    user=Depends(require_token(True)),
):
    """Append chunk. Reads Upload-Offset header."""
    offset_hdr = request.headers.get("Upload-Offset")
    if offset_hdr is None:
        raise HTTPException(400, "missing Upload-Offset header")
    try:
        offset = int(offset_hdr)
    except ValueError:
        raise HTTPException(400, "Upload-Offset must be integer")
    data = await request.body()
    mgr = _get_manager(request)
    try:
        new_offset = mgr.append(upload_id, offset, data)
    except KeyError:
        raise HTTPException(404, "upload session not found")
    except ValueError as e:
        raise HTTPException(409, str(e))
    return {"upload_id": upload_id, "offset": new_offset}


@router.post("/upload/{upload_id}/complete")
async def complete_upload(
    upload_id: str,
    request: Request,
    filename: str = Query(..., description="final filename"),
    user=Depends(require_token(True)),
):
    """Finalize upload: move tmp file to target_dir/filename."""
    mgr = _get_manager(request)
    try:
        final_path = mgr.complete(upload_id, filename)
    except KeyError:
        raise HTTPException(404, "upload session not found")
    except UploadConflictError as e:
        raise HTTPException(409, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"upload_id": upload_id, "final_path": final_path}
