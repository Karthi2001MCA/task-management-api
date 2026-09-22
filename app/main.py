from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401 - registers Task with Base.metadata
from app.database import Base, engine
from app.routers import tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app=FastAPI(
    title="Task Management API",
    description="A simple REST API for managing task",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(tasks.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
