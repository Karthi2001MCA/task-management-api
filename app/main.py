from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import tasks

from app import models  # noqa: F401 - registers Task with Base.metadata
from app.database import Base, engine
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up")
    Base.metadata.create_all(bind=engine)
    yield
    print("Shutting down")

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
    