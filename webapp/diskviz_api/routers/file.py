from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from ..auth import require_token

router = APIRouter()

@router.get("/file/{scan_id}")
async def get_file_meta(scan_id: str, path: str = Query(...),
                        user=Depends(require_token(False))):
    from ..main import app
    mgr = app.state.scan_manager
    if scan_id not in mgr._scans:
        raise HTTPException(404, "scan not found")
    rs = mgr._scans[scan_id]
    cursor = await rs.store._db.execute("SELECT * FROM entries WHERE path=?", (path,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(404, "file not in scan")
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))

@router.get("/file/{scan_id}/content")
async def download_file(scan_id: str, path: str = Query(...),
                        user=Depends(require_token(False))):
    p = Path(path)
    if not p.is_file():
        raise HTTPException(404, "file not found")
    return FileResponse(str(p), filename=p.name)
