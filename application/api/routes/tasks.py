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
from file_io.task_io import load_all_tasks
from file_io.user_io import (
    get_uuid_by_display_name,
    load_users,
)
from services.exp_service import update_user_exp_for_task, deduct_user_exp_for_task
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
        },
        "total_exp": user.get("total_exp", 0)
    }


@router.post("/toggle")
def toggle(data: dict = Body(...)):
    result = toggle_task(data["person"], data["index"])
    if result["task_name"]:
        all_tasks = load_all_tasks()
        task_dict = next((t for t in all_tasks if t.get("name") == result["task_name"]), None)
        if not task_dict:
            return None

        uuid = get_uuid_by_display_name(data["person"])
        if not uuid:
            return None

        if result["completed"]:
            exp_result = update_user_exp_for_task(uuid, task_dict)
            result["exp_gained"] = exp_result["exp_gained"]
            result["total_exp"] = exp_result["total_exp"]
        else:
            exp_result = deduct_user_exp_for_task(uuid, task_dict)
            result["exp_deducted"] = exp_result["exp_deducted"]
            result["total_exp"] = exp_result["total_exp"]
    return result


@router.post("/sync-streak")
def sync_streak(data: dict = Body(...)):
    uuid = str(data.get("uuid", None))
    if uuid is None:
        raise HTTPException(status_code=400, detail="UUID is required")

    user = get_user_or_404(uuid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    file = get_today_file()

    all_completed = check_all_tasks_completed(user['name'], file)
    result = update_user_streak(uuid, all_completed)

    return {
        "status": "ok",
        "current_streak": result["current_streak"],
        "best_streak": result["best_streak"],
        "streak_status": result["status"]  # "active", "broken", "started", "already_done", "not_started"
    }


@router.post("/sync-exp")
def sync_exp(data: dict = Body(...)):
    uuid = str(data.get("uuid", None))
    if uuid is None:
        raise HTTPException(status_code=400, detail="UUID is required")

    user = get_user_or_404(uuid)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    task = ""  # get it from the toggle, this should aonly get called when a task is toggled.
    # also maybe get when untoggle to remove the exp?
    # yeah
    result = update_user_exp_for_task(uuid, task)

    return {
        "status": "ok",
        "total_exp": result["total_exp"],
    }
