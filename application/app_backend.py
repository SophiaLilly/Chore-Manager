# Partial Imports
from datetime import date, datetime, timedelta
from fastapi import HTTPException
from fastapi.security import HTTPBearer
from filelock import FileLock
from pathlib import Path

# Full Imports
import frontmatter
import random
import re


VAULT_PATH = Path("../vault")
CHORES_PATH = VAULT_PATH / "chores"
PEOPLE_PATH = VAULT_PATH / "people"
DATA_PATH = VAULT_PATH / "data"
TASKS_PATH = DATA_PATH / "tasks"
USERS_PATH = DATA_PATH / "users"
VARIABLES_PATH = DATA_PATH / "variables"

TASK_PATTERN = re.compile(r"\d+\.\s*\[([ x])]\s*\[\[(.+?)]]")
TOGGLE_PATTERN = re.compile(r"(\d+\.\s*)\[([ x])](\s*\[\[.+]])")

security = HTTPBearer()


def load_users():
    users = {}
    for file in USERS_PATH.glob("*.md"):
        meta = frontmatter.load(file).metadata
        uuid = meta.get("uuid")
        if uuid:
            users[uuid] = {
                "name": file.stem,
                "display_name": meta.get("display_name"),
                "permissions": meta.get("permissions"),
                "unavailable_days": meta.get("unavailable_days", [])
            }

    return users


def load_tasks(file):
    path = TASKS_PATH / file
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def load_all_tasks():
    file = TASKS_PATH / "tasks.md"
    if not file.exists():
        return []
    return frontmatter.load(file).metadata.get("tasks", [])


def is_user_eligible_for_task(user, task, day_index):
    if day_index in (user.get("unavailable_days") or []):
        return False

    allowed = task.get("allowed_users") or []
    if isinstance(allowed, str):
        allowed = [allowed]

    if allowed and user["display_name"] not in allowed:
        return False

    excluded = task.get("excluded_users") or []
    if isinstance(excluded, str):
        excluded = [excluded]

    if user["display_name"] in excluded:
        return False

    return True


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


def write_tasks_to_file(assignments, filepath):
    today_str = date.today().isoformat()
    lines = [f"# {today_str}", ""]
    for user, tasks in assignments.items():
        lines.append(f"- {user}")
        lines.extend(f"  {i}. [ ] [[{t}]]" for i, t in enumerate(tasks, 1))
        lines.append("")
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text("\n".join(lines))


def parse_date(s: str) -> date:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass

    raise ValueError(f"ERROR: Unrecognized date format: {s}")


def ensure_today_file(users, force=False):
    file = get_today_file()
    with FileLock(str(file) + ".lock"):
        if not file.exists() or force:
            assignments, _ = distribute_tasks_for_today(users)
            if any(assignments.values()) or not file.exists():
                write_tasks_to_file(assignments, file)

    return file


def get_today_file():
    today = date.today()
    y, w, _ = today.isocalendar()
    return CHORES_PATH / str(y) / str(w) / f"{today.isoformat()}.md"


def parse_day(filepath: Path):
    if not filepath.exists():
        return {}

    lines = filepath.read_text().splitlines()

    data = {}
    current_group = None
    task_index = 0

    for line in lines:
        line = line.rstrip()

        if line.startswith("- "):
            current_group = line[2:].strip()
            data[current_group] = []
            task_index = 0
            continue

        if current_group:
            match = TASK_PATTERN.match(line.strip())
            if match and current_group:
                completed = match.group(1) == "x"
                task_name = match.group(2)
                data[current_group].append({
                    "task": task_name,
                    "completed": completed,
                    "index": task_index
                })
                task_index += 1

    return data


def toggle_task(person: str, task_index: int):
    file = get_today_file()
    with FileLock(str(file) + ".lock"):
        if not file.exists():
            raise HTTPException(status_code=404, detail="No file for today") ## Realistically this should be impossible because if nothing loads, there would be no tasks to toggle, but we ball.

        lines = file.read_text().splitlines()
        current = None
        counter = -1
        completed = False

        for i, line in enumerate(lines):
            if line.startswith("- "):
                current = line[2:].strip()
                counter = -1
                continue

            match = TOGGLE_PATTERN.match(line.strip())
            if not match or current != person:
                continue

            counter += 1
            if counter != task_index:
                continue

            new = " " if match.group(2) == "x" else "x"
            lines[i] = f"  {match.group(1)}[{new}]{match.group(3)}"
            completed = new == "x"
            break

        file.write_text("\n".join(lines))
    return {"status": "ok", "completed": completed}


def check_all_tasks_completed(person: str, filepath: Path) -> bool:
    if not filepath.exists():
        return False
    
    tasks_data = parse_day(filepath)
    person_tasks = tasks_data.get(person, [])

    if not person_tasks:
        return True

    return all(task.get("completed", False) for task in person_tasks)


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

    yesterday_file = CHORES_PATH / str(yesterday.isocalendar()[0]) / str(yesterday.isocalendar()[1]) / f"{yesterday.isoformat()}.md"

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
            current_streak = 0  # 🔥 break streak ONLY here

        metadata["current_streak"] = current_streak
        metadata["last_streak_check"] = today.isoformat()

        post.metadata = metadata
        user_file.write_text(frontmatter.dumps(post))


def get_user_streak(user_uuid: str) -> dict:
    """
    Retrieve a user's current streak statistics.
    
    Returns:
        {"current_streak": int, "best_streak": int, "last_completion_date": str}
    """
    users = load_users()
    if user_uuid not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_name = users[user_uuid]["name"]
    user_file = USERS_PATH / f"{user_name}.md"
    
    post = frontmatter.load(user_file)
    metadata = post.metadata
    
    return {
        "current_streak": metadata.get("current_streak", 0),
        "best_streak": metadata.get("best_streak", 0),
        "last_completion_date": metadata.get("last_completion_date", None)
    }


def migrate_users_to_streak_system():
    """Add streak fields to all user files that don't have them."""
    for file in USERS_PATH.glob("*.md"):
        post = frontmatter.load(file)
        if "current_streak" not in post.metadata:
            post.metadata["current_streak"] = 0
            post.metadata["best_streak"] = 0
            post.metadata["last_completion_date"] = None
            post.metadata["last_streak_check"] = None
            file.write_text(frontmatter.dumps(post))
            print(f"Migrated: {file.stem}")
    print("Migration complete")


if __name__ == "__main__":
    elodie_uuid = "f4842ac8-e5ef-4029-9bab-7b52cc5b1088"
    update_user_streak(elodie_uuid, check_all_tasks_completed("Elodie", get_today_file()))
    migrate_users_to_streak_system()
