from sqlalchemy.orm import Session
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate
from sqlalchemy import select

def create_task(db:Session,task_in: TaskCreate) -> Task:
    task = Task(**task_in.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_tasks(db: Session) -> list[Task]:
    return list(db.scalars(select(Task).order_by(Task.id)))


def get_task(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)

def update_task(db: Session, task: Task, task_in: TaskUpdate) -> Task:
    for field, value in task_in.model_dump().items():
        setattr(task,field,value)
    db.commit()
    db.refresh(task)
    return task

def delete_task(_db: Session,task: Task) -> Task:
    _db.delete(task)
    _db.commit()
    return task