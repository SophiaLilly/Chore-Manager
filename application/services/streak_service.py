# application/services/streak_service.py

# Local Internal Imports
from services.task_service import check_all_tasks_completed

# Local External Imports
from core.config import (
    USERS_PATH,
    CHORES_PATH,
)
from file_io.user_io import load_users

# Partial Imports
from datetime import (
    date,
    timedelta,
)
from fastapi import HTTPException
from filelock import FileLock

# Full Imports
import frontmatter


def update_user_streak(user_uuid: str, completed: bool) -> dict:
    users = load_users()
    if user_uuid not in users:
        raise HTTPException(status_code=404, detail="User not found")

    user_name = users[user_uuid]["name"]
    user_file = USERS_PATH / f"{user_name}.md"

    with FileLock(str(user_file) + ".lock"):
        post = frontmatter.load(user_file)
        metadata = post.metadata

        today = date.today().isoformat()
        last_completion = metadata.get("last_completion_date")
        current_streak = metadata.get("current_streak", 0)
        best_streak = metadata.get("best_streak", 0)

        if completed:
            if last_completion == today:
                status = "already_done"
            elif last_completion == (date.today() - timedelta(days=1)).isoformat():
                current_streak += 1
                best_streak = max(current_streak, best_streak)
                status = "active"
            else:
                current_streak = 1
                status = "started"

            metadata["last_completion_date"] = today
        else:
            status = "incomplete"

        metadata["current_streak"] = current_streak
        metadata["best_streak"] = best_streak
        post.metadata = metadata
        user_file.write_text(frontmatter.dumps(post))

    return {
        "current_streak": current_streak,
        "best_streak": best_streak,
        "status": status
    }


def evaluate_streak_for_new_day(user_uuid: str):
    users = load_users()
    if user_uuid not in users:
        raise HTTPException(status_code=404, detail="User not found")

    user = users[user_uuid]
    user_name = user["name"]
    display_name = user["display_name"]

    user_file = USERS_PATH / f"{user_name}.md"

    today = date.today()
    yesterday = today - timedelta(days=1)

    yesterday_file = CHORES_PATH / str(yesterday.isocalendar()[0]) / str \
        (yesterday.isocalendar()[1]) / f"{yesterday.isoformat()}.md"

    with FileLock(str(user_file) + ".lock"):
        post = frontmatter.load(user_file)
        metadata = post.metadata

        last_checked = metadata.get("last_streak_check")

        # Prevent double-processing the same day
        if last_checked == today.isoformat():
            return

        # Check yesterday completion
        completed = check_all_tasks_completed(display_name, yesterday_file)

        current_streak = metadata.get("current_streak", 0)

        if not completed and current_streak > 0:
            current_streak = 0

        metadata["current_streak"] = current_streak
        metadata["last_streak_check"] = today.isoformat()

        post.metadata = metadata
        user_file.write_text(frontmatter.dumps(post))
