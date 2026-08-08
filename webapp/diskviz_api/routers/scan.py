import hashlib
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, Query
from pydantic import BaseModel
from ..auth import require_token, verify_confirm_token
from ..config import settings

router = APIRouter()

class ScanRequest(BaseModel):
    root: str
    workers: int = 0

def _get_manager():
    from ..main import app
    return app.state.scan_manager

@router.post("/scan")
async def start_scan(req: ScanRequest, user=Depends(require_token(False))):
    mgr = _get_manager()
    # Check max concurrent
    running = sum(1 for rs in mgr._scans.values() if not rs.finished)
    if running >= settings.max_concurrent_scans:
        raise HTTPException(409, "another scan in progress")
    scan_id = await mgr.start(req.root, req.workers)
    return {"scan_id": scan_id}

@router.get("/scan/{scan_id}")
async def get_scan_status(scan_id: str, user=Depends(require_token(False))):
    mgr = _get_manager()
    if scan_id not in mgr._scans:
        raise HTTPException(404, "scan not found")
    rs = mgr._scans[scan_id]
    return {
        "scan_id": scan_id, "root": rs.root, "started_at": rs.started_at,
        "finished": rs.finished, "result": rs.result,
        "last_progress": rs.last_progress,
    }

@router.delete("/scan/{scan_id}")
async def cancel_scan(scan_id: str, user=Depends(require_token(True))):
    mgr = _get_manager()
    if scan_id not in mgr._scans:
        raise HTTPException(404, "scan not found")
    rs = mgr._scans[scan_id]
    if rs.proc and rs.proc.returncode is None:
        rs.proc.terminate()
    return {"cancelled": True}

@router.websocket("/ws/scan/{scan_id}")
async def scan_ws(ws: WebSocket, scan_id: str, token: str = Query(default="")):
    token_sha = hashlib.sha256(token.encode()).hexdigest()
    if token_sha not in (settings.read_token_sha256, settings.write_token_sha256):
        await ws.close(code=4001, reason="invalid token")
        return
    mgr = _get_manager()
    if scan_id not in mgr._scans:
        await ws.close(code=4004, reason="scan not found")
        return
    await ws.accept()
    try:
        async for frame in mgr.subscribe(scan_id):
            await ws.send_json(frame)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
