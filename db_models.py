# models.py
from typing import Optional, List
from sqlmodel import SQLModel, Field
from datetime import date
from sqlalchemy import Column, JSON

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    category: Optional[str] = Field(default="Miscellaneous")
    deadline: Optional[str] = None
    # store subtasks as JSON array
    subtasks: Optional[List[str]] = Field(
        default_factory=list,
        sa_column=Column(JSON)
    )

