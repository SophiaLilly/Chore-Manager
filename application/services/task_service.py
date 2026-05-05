# application/services/task_service.py

# Local Internal Imports
from user_service import is_user_eligible_for_task

# Local External Imports
from application.core.config import TASKS_PATH
from application.file_io.chores_io import (
    get_today_file,
    parse_day,
    write_chores_to_file,
)
from application.utils.date_utils import parse_date


# Partial Imports
from datetime import date
from filelock import FileLock
from pathlib import Path

# Full Imports
import frontmatter
import random


def distribute_tasks_for_today(users):
    file = TASKS_PATH / "tasks.md"
    today_str = date.today().isoformat()
    day_index = date.today().weekday()

    with FileLock(str(file) + ".lock"):
        post = frontmatter.load(file)
        tasks = post.metadata.get("tasks", [])

        pool = [t for t in tasks if should_add_to_pool(t)]

    random.shuffle(pool)

    user_list = list(users.values())

    assignments = {user["display_name"]: [] for user in user_list}
    load = {user["display_name"]: 0 for user in user_list}

    skipped_tasks = []

    def get_difficulty(task):
        try:
            return int(task.get("difficulty", 1))
        except Exception:
            return 1

    for task in sorted(pool, key=lambda t: -get_difficulty(t)):
        task_name = task.get("name", "UNKNOWN TASK")

        eligible_users = [
            user for user in user_list
            if is_user_eligible_for_task(user, task, day_index)
        ]

        if not eligible_users:
            print(f"Skipping task '{task_name}' - no eligible users")
            skipped_tasks.append(task_name)
            continue

        min_load = min(load[u["display_name"]] for u in eligible_users)

        candidates = [
            u for u in eligible_users
            if load[u["display_name"]] == min_load
        ]

        chosen = random.choice(candidates)

        name = chosen["display_name"]
        diff = get_difficulty(task)

        assignments[name].append(task_name)
        load[name] += diff

        task["last_added"] = today_str

    with FileLock(str(file) + ".lock"):
        post.metadata["tasks"] = tasks
        file.write_text(frontmatter.dumps(post))

    if not pool:
        print("WARNING: Task pool is empty")

    return assignments, skipped_tasks


def ensure_today_file(users, force=False):
    file = get_today_file()
    with FileLock(str(file) + ".lock"):
        if not file.exists() or force:
            assignments, _ = distribute_tasks_for_today(users)
            if any(assignments.values()) or not file.exists():
                write_chores_to_file(assignments, file)

    return file


def reset_all_last_added():
    file = TASKS_PATH / "tasks.md"
    with FileLock(str(file) + ".lock"):
        if not file.exists():
            print("tasks.md not found")
            return
        post = frontmatter.load(file)
        tasks = post.metadata.get("tasks", [])
        for t in tasks:
            t["last_added"] = "2000-01-01"
        post.metadata["tasks"] = tasks
        file.write_text(frontmatter.dumps(post))
    print("All last_added values reset.")


def should_add_to_pool(task):
    today = date.today()
    today_day = today.weekday()
    allowed_days = task.get("allowed_days")
    if allowed_days is not None:
        try:
            if today_day not in map(int, allowed_days):
                return False
        except Exception:
            print(f"Bad allowed_days in task: {task.get('name')}")
            return False

    last = task.get("last_added")
    if last is None:
        return True
    interval = task.get("every_x_days", 1)
    return (today - parse_date(last)).days >= interval


def check_all_tasks_completed(person: str, filepath: Path) -> bool:
    if not filepath.exists():
        return False

    tasks_data = parse_day(filepath)
    person_tasks = tasks_data.get(person, [])

    if not person_tasks:
        return True

    return all(task.get("completed", False) for task in person_tasks)
