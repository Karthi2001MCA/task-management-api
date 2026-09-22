from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401 - registers Task with Base.metadata
from app.config import PROJECT_ROOT
from app.database import Base, engine
from app.routers import tasks

STATIC_DIR = PROJECT_ROOT / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Task Management API",
    description="A simple REST API for managing tasks",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(tasks.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def index():
    """Serve the browser UI."""
    return FileResponse(STATIC_DIR / "index.html")
