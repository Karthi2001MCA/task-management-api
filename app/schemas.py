from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskBase):
    pass


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
