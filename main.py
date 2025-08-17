from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List
from database import init_db, get_session
from db_models import Task
from pydantic import BaseModel
from datetime import date
from suggest import router as suggest_router

app = FastAPI(title="GenAI Productivity Assistant")

@app.get("/")
def root():
    return {"message": "Welcome to the Productivity Assistant API"}

# CORS settings
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI backend!"}

# Initialize database
init_db()

# Dependency to get DB session
def get_db():
    with Session(init_db.engine) as session:
        yield session

@app.get("/health")
def health():
    return {"status": "ok", "app": "AI Task Manager API"}

# Pydantic model for create/update requests (exclude id, created_at)
class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    category: str | None = "Miscellaneous"
    deadline: date | None = None
    subtasks: List[str] | None = []

class TaskRead(BaseModel):
    id: int
    title: str
    description: str | None
    category: str | None
    deadline: date | None
    subtasks: List[str] | None

@app.post("/tasks/", response_model=TaskRead)
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    db_task = Task.from_orm(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@app.get("/tasks/", response_model=List[TaskRead])
def read_tasks(session: Session = Depends(get_session)):
    tasks = session.exec(select(Task)).all()
    return tasks

@app.get("/tasks/{task_id}", response_model=TaskRead)
def read_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, task_update: TaskCreate, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in task_update.dict(exclude_unset=True).items():
        setattr(task, key, value)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return None

# Include your suggest router
app.include_router(suggest_router, prefix="/api")  # optional prefix