import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import health, scan, tree, file, ops, archive, upload, reports
from .services.scanner_runner import ScanManager
from .services.archive import ArchiveManager
from .services.upload import UploadManager
from .services.dup_detector import DupDetector

logger = logging.getLogger(__name__)


def cleanup_once(scans_dir: Path, ttl_seconds: int) -> int:
    """One-shot cleanup. Deletes *.sqlite files older than ttl. Returns count deleted."""
    scans_dir = Path(scans_dir)
    if not scans_dir.exists():
        return 0
    cutoff = time.time() - ttl_seconds
    deleted = 0
    for f in scans_dir.iterdir():
        if not f.is_file() or f.suffix != ".sqlite":
            continue
        try:
            mtime = f.stat().st_mtime
        except OSError:
            continue
        if mtime < cutoff:
            try:
                f.unlink()
                deleted += 1
            except OSError:
                pass
    return deleted


async def cleanup_expired_scans(interval_seconds: int = 300) -> None:
    """Periodic cleanup loop. Runs every interval_seconds."""
    while True:
        try:
            await asyncio.to_thread(cleanup_once, settings.scans_dir, settings.scan_ttl_seconds)
        except Exception:
            logger.exception("cleanup iteration failed")
        await asyncio.sleep(interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not hasattr(app.state, "scan_manager"):
        app.state.scan_manager = ScanManager()
    if not hasattr(app.state, "archive_manager"):
        app.state.archive_manager = ArchiveManager(scans_dir=settings.scans_dir)
    if not hasattr(app.state, "upload_manager"):
        app.state.upload_manager = UploadManager(scans_dir=settings.scans_dir)
    if not hasattr(app.state, "dup_detector"):
        app.state.dup_detector = DupDetector()
    app.state.cleanup_task = asyncio.create_task(cleanup_expired_scans())
    try:
        yield
    finally:
        app.state.cleanup_task.cancel()
        try:
            await app.state.cleanup_task
        except asyncio.CancelledError:
            pass
        await app.state.scan_manager.cancel_all()

app = FastAPI(title="diskviz", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(scan.router)
app.include_router(tree.router)
app.include_router(file.router)
app.include_router(ops.router)
app.include_router(archive.router)
app.include_router(upload.router)
app.include_router(reports.router)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

def main():
    import uvicorn
    uvicorn.run(app, host=settings.bind_host, port=settings.bind_port, workers=1)
