from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import settings
from .routers import health, scan, tree, file, ops
from .services.scanner_runner import ScanManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not hasattr(app.state, "scan_manager"):
        app.state.scan_manager = ScanManager()
    yield
    await app.state.scan_manager.cancel_all()

app = FastAPI(title="diskviz", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(scan.router)
app.include_router(tree.router)
app.include_router(file.router)
app.include_router(ops.router)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

def main():
    import uvicorn
    uvicorn.run(app, host=settings.bind_host, port=settings.bind_port, workers=1)
