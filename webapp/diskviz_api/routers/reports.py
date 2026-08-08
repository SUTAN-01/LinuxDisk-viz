import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..auth import require_token

router = APIRouter()


def _csv_sanitize(value: str) -> str:
    """Guard against CSV formula injection by prefixing dangerous leading chars."""
    if value and value[0] in ("=", "+", "-", "@"):
        return "\t" + value
    return value


def _get_manager():
    from ..main import app
    return app.state.scan_manager


def _get_detector():
    from ..main import app
    return app.state.dup_detector


def _get_store(scan_id: str):
    mgr = _get_manager()
    if scan_id not in mgr._scans:
        raise HTTPException(404, "scan not found")
    rs = mgr._scans[scan_id]
    if rs.store is None:
        raise HTTPException(409, "scan store not ready")
    return rs.store


@router.get("/reports/top-large/{scan_id}")
async def top_large(
    scan_id: str,
    limit: int = Query(100, ge=1, le=10000),
    min_size: int = Query(0, ge=0),
    user=Depends(require_token(False)),
):
    store = _get_store(scan_id)
    rows = await store.get_top_large(scan_id, limit, min_size)
    return {"entries": rows, "count": len(rows)}


@router.post("/reports/duplicates/{scan_id}")
async def start_dup_detection(
    scan_id: str,
    min_size: int = Query(0, ge=0),
    user=Depends(require_token(False)),
):
    store = _get_store(scan_id)
    rows = await store.get_top_large(scan_id, limit=100000, min_size=min_size)
    paths = [r["path"] for r in rows]
    detector = _get_detector()
    job_id = detector.start_job(paths, min_size)
    return {"job_id": job_id, "status": "running", "paths_count": len(paths)}


@router.get("/reports/duplicates/{scan_id}/{job_id}")
async def dup_status(
    scan_id: str,
    job_id: str,
    user=Depends(require_token(False)),
):
    # validate scan exists (but don't require store, since job may outlive it)
    mgr = _get_manager()
    if scan_id not in mgr._scans:
        raise HTTPException(404, "scan not found")
    detector = _get_detector()
    try:
        return detector.get_status(job_id)
    except KeyError:
        raise HTTPException(404, "job not found")


@router.get("/reports/export/{scan_id}")
async def export(
    scan_id: str,
    fmt: str = Query("csv", pattern="^(csv|json)$"),
    user=Depends(require_token(False)),
):
    store = _get_store(scan_id)
    rows = await store.get_top_large(scan_id, limit=100000, min_size=0)
    if fmt == "json":
        content = json.dumps(rows, ensure_ascii=False, indent=2)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={scan_id}.json"},
        )
    # csv
    buf = io.StringIO()
    fieldnames = list(rows[0].keys()) if rows else ["path"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: _csv_sanitize(str(v)) for k, v in r.items()})
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={scan_id}.csv"},
    )
