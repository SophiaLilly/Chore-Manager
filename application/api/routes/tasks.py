# applications/api/routes/tasks.py

# Local Internal Imports
from api.deps import get_user_or_404

# Local External Imports
from file_io.chores_io import (
    get_today_file,
    parse_day,
    toggle_task,
)
from file_io.streak_io import get_user_streak
from file_io.user_io import load_users

from services.streak_service import (
    evaluate_streak_for_new_day,
    update_user_streak,
)
from services.task_service import (
    check_all_tasks_completed,
    ensure_today_file,
)

# Partial Imports
from fastapi import (
    APIRouter,
    Body,
    Query,
    HTTPException,
)


router = APIRouter()


@router.get("/today")
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
        "status": "ok",
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


@router.post("/toggle")
def toggle(data: dict = Body(...)):
    toggle_task(data["person"], data["index"])
    return {"status": "ok"}


@router.post("/sync-streak")
def sync_streak(data: dict = Body(...)):
    uuid = data.get("uuid")
    if uuid is None:
        raise HTTPException(status_code=400, detail="UUID is required")

    users = load_users()
    if users is None:
        raise HTTPException(status_code=400, detail="Users are not available")

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
