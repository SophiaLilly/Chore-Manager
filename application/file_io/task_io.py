# application/file_io/task_io.py

# Local External Imports
from core.config import TASKS_PATH

# Full Imports
import frontmatter


def save_tasks(tasks):
    file = TASKS_PATH / "tasks.md"
    post = frontmatter.load(file)
    post.metadata["tasks"] = tasks
    file.write_text(frontmatter.dumps(post))


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
