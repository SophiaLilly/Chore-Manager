# app_runtime.py

# Local Imports
from app_backend import *

# Partial Imports
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from filelock import FileLock
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from uvicorn import Config, Server

# Full Imports
import asyncio
import frontmatter
import re


BASE_PATH = Path(__file__).resolve().parent.parent
VAULT_PATH = BASE_PATH / "vault"
DATA_PATH = VAULT_PATH / "data"
TASKS_PATH = DATA_PATH / "tasks"

api = FastAPI(title="Chore Manager API", version="0.1.0")
api.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chores.lillywhite.dev",
        "https://lillywhite.dev",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


def get_user_or_404(uuid: str):
    users = load_users()
    user = users.get(uuid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def require_admin(uuid: str):
    user = get_user_or_404(uuid)
    permissions = user.get("permissions") or []
    if "admin" not in permissions:
        raise HTTPException(status_code=403, detail="Admin permissions required")
    return user


def save_tasks(tasks):
    file = TASKS_PATH / "tasks.md"
    post = frontmatter.load(file)
    post.metadata["tasks"] = tasks
    file.write_text(frontmatter.dumps(post))


@api.get("/")
def root():
    return {"status": "Chore Manager Backend is running"}


@api.get("/today")
def get_today(uuid: str = Query(...)):
    user = get_user_or_404(uuid)
    evaluate_streak_for_new_day(uuid)

    users = load_users()
    file = ensure_today_file(users, force=False)
    tasks = parse_day(file)

    permissions = user.get("permissions") or []
    is_admin = "admin" in permissions

    streak = get_user_streak(uuid)
    all_completed = check_all_tasks_completed(user.get("display_name"), file)

    return {
        "user": user["display_name"],
        "tasks": tasks.get(user["display_name"], []),
        "all_tasks": tasks,
        "is_admin": is_admin,
        "streak": {
            "current": streak["current_streak"],
            "best": streak["best_streak"],
            "all_tasks_completed_today": all_completed
        }
    }


@api.get("/health")
def health():
    return {"status": "ok"}


@api.post("/toggle")
def toggle(data: dict = Body(...)):
    person = data["person"]
    index = data["index"]
    toggle_task(person, index)
    return {"status": "ok"}


@api.post("/sync-streak")
def sync_streak(data: dict = Body(...)):
    uuid = data.get("uuid")
    users = load_users()
    if uuid not in users:
        raise HTTPException(status_code=404, detail="User not found")

    user = users[uuid]
    file = get_today_file()

    all_completed = check_all_tasks_completed(user["display_name"], file)
    result = update_user_streak(uuid, all_completed)

    return {
        "status": "ok",
        "current_streak": result["current_streak"],
        "best_streak": result["best_streak"],
        "streak_status": result["status"]  # "active", "broken", "started", "already_done", "not_started"
    }


@api.get("/admin/verify")
def verify_admin(uuid: str):
    user = get_user_or_404(uuid)
    permissions = user.get("permissions") or []

    return {
        "is_admin": "admin" in permissions,
        "user": user.get("display_name")
    }


# TODO: refactor
@api.get("/admin/pools")
def get_pools(uuid: str):
    users = load_users()

    if uuid not in users:
        raise HTTPException(404)

    user = users[uuid]
    permissions = user.get("permissions") or []
    if "admin" not in permissions:
        return {"is_admin": False}

    return {
        "is_admin": True,
        "daily": load_tasks("daily_pool.md"),
        "weekly": load_tasks("weekly_pool.md"),
        "monthly": load_tasks("monthly_pool.md")
    }


@api.get("/admin/tasks")
def get_tasks(uuid: str):
    require_admin(uuid)
    return {"tasks": load_all_tasks()}


@api.post("/admin/tasks/add")
def add_task(data: dict = Body(...)):
    require_admin(data["uuid"])

    file = TASKS_PATH / "tasks.md"
    post = frontmatter.load(file)

    tasks = post.metadata.get("tasks", [])
    tasks.append(data["task"])

    post.metadata["tasks"] = tasks
    file.write_text(frontmatter.dumps(post))

    return {"status": "ok"}


@api.post("/admin/tasks/delete")
def delete_task(data: dict = Body(...)):
    require_admin(data["uuid"])

    file = TASKS_PATH / "tasks.md"
    post = frontmatter.load(file)

    tasks = post.metadata.get("tasks", [])
    tasks.pop(data["index"])

    post.metadata["tasks"] = tasks
    file.write_text(frontmatter.dumps(post))

    return {"status": "ok"}


@api.post("/admin/tasks/update")
def update_task(req: UpdateRequest):
    require_admin(req.uuid)

    tasks = load_all_tasks()

    if req.index < 0 or req.index >= len(tasks):
        raise HTTPException(status_code=400, detail="Invalid index")

    tasks[req.index] = {
        "name": req.task.name,
        "difficulty": req.task.difficulty,
        "every_x_days": req.task.every_x_days,
        "allowed_days": req.task.allowed_days,
        "last_added": req.task.last_added
    }

    file = TASKS_PATH / "tasks.md"
    with FileLock(str(file) + ".lock"):
        post = frontmatter.load(file)
        post.metadata["tasks"] = tasks
        file.write_text(frontmatter.dumps(post))


    return {"success": True}


@api.post("/admin/reset_tasks")
def reset_tasks(data: dict = Body(...)):
    require_admin(data["uuid"])
    reset_all_last_added()
    return {"status": "reset"}


@api.get("/admin/todo")
def get_todo(uuid: str):
    require_admin(uuid)

    file = VAULT_PATH / "todo.md"
    if not file.exists():
        return {"items": []}
    items = []

    for i, line in enumerate(file.read_text().splitlines()):
        match = re.match(r"\[([ x])]\s*(.+)", line)
        if match:
            items.append({
                "text": match.group(2),
                "completed": match.group(1) == "x",
                "index": i
            })

    return {"items": items}


@api.post("/admin/todo/add")
def add_todo(data: dict = Body(...)):
    require_admin(data["uuid"])

    file = VAULT_PATH / "todo.md"
    with open(file, "a") as f:
        f.write(f"\n[ ] {data['text']}")

    return {"status": "ok"}


@api.post("/admin/todo/toggle")
def toggle_todo(data: dict = Body(...)):
    require_admin(data["uuid"])

    file = VAULT_PATH / "todo.md"

    lines = file.read_text().splitlines()
    index = data.get("index")
    if not isinstance(index, int):
        raise HTTPException(404, "Invalid index")
    line = lines[index]

    match = re.match(r"\[([ x])](\s*.+)", line)
    if match:
        new_state = " " if match.group(1) == "x" else "x"
        lines[data["index"]] = f"[{new_state}]{match.group(2)}"

    file.write_text("\n".join(lines))

    return {"status": "ok"}


@api.post("/admin/todo/delete")
def delete_todo(data: dict = Body(...)):
    require_admin(data["uuid"])

    file = VAULT_PATH / "todo.md"
    lines = file.read_text().splitlines()

    lines.pop(data["index"])

    file.write_text("\n".join(lines))

    return {"status": "ok"}


async def main():
    config = Config(
        app="app_runtime:api",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True,
        reload_dirs=["."]
    )
    server = Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
