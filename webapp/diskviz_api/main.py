from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .routers import health

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="diskviz", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

def main():
    import uvicorn
    from .config import settings
    uvicorn.run(app, host=settings.bind_host, port=settings.bind_port, workers=1)
