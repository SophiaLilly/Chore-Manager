# application/api/routes/admin.py

# Local Internal Imports
from api.deps import require_admin, get_user_or_404

# Local External Imports
from application.core.config import (
    TASKS_PATH,
    VAULT_PATH,
)
from file_io.task_io import load_all_tasks
from models.schemas import UpdateRequest
from services.task_service import reset_all_last_added

# Partial Imports
from fastapi import (
    APIRouter,
    Body,
    HTTPException,
)
from filelock import FileLock

# Full Imports
import frontmatter
import re


router = APIRouter(prefix="/admin")


@router.get("/admin/verify")
def verify_admin(uuid: str):
    user = get_user_or_404(uuid)
    permissions = user.get("permissions") or []

    return {
        "is_admin": "admin" in permissions,
        "user": user.get("display_name")
    }


@router.get("/admin/tasks")
def get_tasks(uuid: str):
    require_admin(uuid)
    return {"tasks": load_all_tasks()}


@router.post("/admin/tasks/add")
def add_task(data: dict = Body(...)):
    require_admin(data["uuid"])

    file = TASKS_PATH / "tasks.md"
    post = frontmatter.load(file)

    tasks = post.metadata.get("tasks", [])
    tasks.append(data["task"])

    post.metadata["tasks"] = tasks
    file.write_text(frontmatter.dumps(post))

    return {"status": "ok"}


@router.post("/admin/tasks/delete")
def delete_task(data: dict = Body(...)):
    require_admin(data["uuid"])

    file = TASKS_PATH / "tasks.md"
    post = frontmatter.load(file)

    tasks = post.metadata.get("tasks", [])
    tasks.pop(data["index"])

    post.metadata["tasks"] = tasks
    file.write_text(frontmatter.dumps(post))

    return {"status": "ok"}


@router.post("/admin/tasks/update")
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


@router.post("/admin/reset_tasks")
def reset_tasks(data: dict = Body(...)):
    require_admin(data["uuid"])
    reset_all_last_added()
    return {"status": "reset"}


@router.get("/admin/todo")
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


@router.post("/admin/todo/add")
def add_todo(data: dict = Body(...)):
    require_admin(data["uuid"])

    file = VAULT_PATH / "todo.md"
    with open(file, "a") as f:
        f.write(f"\n[ ] {data['text']}")

    return {"status": "ok"}


@router.post("/admin/todo/toggle")
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


@router.post("/admin/todo/delete")
def delete_todo(data: dict = Body(...)):
    require_admin(data["uuid"])

    file = VAULT_PATH / "todo.md"
    lines = file.read_text().splitlines()

    lines.pop(data["index"])

    file.write_text("\n".join(lines))

    return {"status": "ok"}
