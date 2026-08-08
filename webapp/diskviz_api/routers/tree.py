from fastapi import APIRouter, Depends, HTTPException, Query
from ..auth import require_token

router = APIRouter()

@router.get("/tree/{scan_id}")
async def get_tree(scan_id: str,
                   path: str = Query(default="/"),
                   depth: int = Query(default=1, ge=1, le=5),
                   limit: int = Query(default=500, ge=1, le=5000),
                   user=Depends(require_token(False))):
    from ..main import app
    mgr = app.state.scan_manager
    if scan_id not in mgr._scans:
        raise HTTPException(404, "scan not found")
    rs = mgr._scans[scan_id]
    if not rs.store:
        raise HTTPException(409, "scan not ready")
    entries = await rs.store.get_children(scan_id, path, limit=limit)
    return {"scan_id": scan_id, "path": path, "entries": entries}
