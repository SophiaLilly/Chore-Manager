# application/file_io/chores_io.py

# Local External Imports
from core.config import CHORES_PATH
from util.task_parsing import TASK_PATTERN, TOGGLE_PATTERN

# Partial Imports
from datetime import date
from fastapi import HTTPException
from filelock import FileLock
from pathlib import Path


def get_today_file():
    today = date.today()
    y, w, _ = today.isocalendar()
    return CHORES_PATH / str(y) / str(w) / f"{today.isoformat()}.md"


def write_chores_to_file(assignments, filepath):
    today_str = date.today().isoformat()
    lines = [f"# {today_str}", ""]
    for user, tasks in assignments.items():
        lines.append(f"- {user}")
        lines.extend(f"  {i}. [ ] [[{t}]]" for i, t in enumerate(tasks, 1))
        lines.append("")
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text("\n".join(lines))


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
    return {
        "status": "ok",
        "completed": completed
    }
