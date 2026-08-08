from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import settings
from .routers import health, scan, tree, file, ops, archive, upload, reports
from .services.scanner_runner import ScanManager
from .services.archive import ArchiveManager
from .services.upload import UploadManager
from .services.dup_detector import DupDetector

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
    yield
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
