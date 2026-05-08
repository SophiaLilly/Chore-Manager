# application/file_io/chores_io.py

# Local External Imports
from core.config import CHORES_PATH
from util.task_parsing import (
    TASK_PATTERN,
    TOGGLE_PATTERN,
)

# Partial Imports
from datetime import date
from fastapi import HTTPException
from filelock import FileLock
from pathlib import Path


def get_today_file():
    return _get_chores_file_for_date(date.today())


def _get_chores_file_for_date(target_date: date) -> Path:
    y, w, _ = target_date.isocalendar()
    return CHORES_PATH / str(y) / str(w) / f"{target_date.isoformat()}.md"


def write_chores_to_file(assignments, filepath):
    content = _format_chores(assignments)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content)


def _format_chores(assignments) -> str:
    today_str = date.today().isoformat()
    lines = [f"# {today_str}", ""]
    for user, tasks in assignments.items():
        lines.append(f"- {user}")
        lines.extend(_format_task_lines(tasks))
        lines.append("")

    return "\n".join(lines)


def _format_task_lines(tasks: list[str]) -> list[str]:
    return [
        f"  {i}. [ ] [[{task}]]"
        for i, task in enumerate(tasks, 1)
    ]


def parse_day(filepath: Path):
    if not filepath.exists():
        return {}

    lines = filepath.read_text().splitlines()
    return _parse_lines(lines)


def _parse_lines(lines: list[str]) -> dict:
    data = {}
    current_group = None
    task_index = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            current_group = stripped[2:].strip()
            data[current_group] = []
            task_index = 0
            continue

        if not current_group:
            continue

        task = _parse_task_line(stripped, task_index)
        if task is None:
            continue

        data[current_group].append(task)
        task_index += 1

    return data


def _parse_task_line(line: str, task_index: int) -> dict | None:
    match = TASK_PATTERN.match(line)
    if not match:
        return None

    return {
        "task": match.group(2),
        "completed": match.group(1) == "x",
        "index": task_index
    }


def toggle_task(person: str, task_index: int):
    file = get_today_file()
    with FileLock(str(file) + ".lock"):
        lines = _load_today_lines(file)
        lines, completed, task_name = _toggle_task_in_lines(lines, person, task_index)
        _save_today_lines(file, lines)

    return {
        "status": "ok",
        "completed": completed,
        "task_name": task_name
    }


def _load_today_lines(file: Path) -> list[str]:
    if not file.exists():
        raise HTTPException(status_code=404, detail="No file for today")
    return file.read_text().splitlines()


def _save_today_lines(file: Path, lines: list[str]):
    file.write_text("\n".join(lines))


def _toggle_task_in_lines(lines: list[str], person: str, task_index: int):
    current = None
    counter = -1

    for i, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if stripped.startswith("- "):
            current = stripped[2:].strip()
            counter = -1
            continue

        if current != person:
            continue

        match = TOGGLE_PATTERN.match(stripped)
        if not match:
            continue

        counter += 1
        if counter != task_index:
            continue

        new_state = " " if match.group(2) == "x" else "x"
        lines[i] = f"  {match.group(1)}[{new_state}]{match.group(3)}"

        task_name_match = TASK_PATTERN.match(raw_line.strip())
        task_name = task_name_match.group(2) if task_name_match else None

        return lines, (new_state == "x"), task_name

    return lines, False, None
