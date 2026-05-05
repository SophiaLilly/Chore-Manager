# application/models/schemas.py

# Partial Imports
from pydantic import BaseModel
from typing import Optional


class TaskModel(BaseModel):
    name: str
    difficulty: int = 1
    every_x_days: int = 1
    allowed_days: Optional[list[int]] = None
    last_added: Optional[str] = None


class UpdateRequest(BaseModel):
    uuid: str
    index: int
    task: TaskModel
