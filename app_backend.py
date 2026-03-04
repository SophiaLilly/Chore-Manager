# Partial Imports
import hashlib
from datetime import date, datetime
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pathlib import Path

# Full Imports
import frontmatter
import re

VAULT_PATH = Path("vault")
CHORES_PATH = VAULT_PATH / "chores"
PEOPLE_PATH = VAULT_PATH / "people"
DATA_PATH = VAULT_PATH / "data"
VARIABLES_PATH = DATA_PATH / "variables"
USERS_PATH = DATA_PATH / "users"

security = HTTPBearer()


def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


def load_users():
    users = {}

    for file in USERS_PATH.glob("*.md"):
        name = file.stem
        post = frontmatter.load(file)
        pin_hash = post.metadata.get("pin_hash")

        if pin_hash:
            users[name] = {"pin_hash": pin_hash}

    return users


def get_secret_key():
    secret_file = VARIABLES_PATH / "SECRET_KEY.md"
    if not secret_file.exists():
        raise FileNotFoundError("Secret key file not found. Please create vault/data/secret.key with a random string.")
    return secret_file.read_text().strip()


def get_algorithm():
    alg_file = VARIABLES_PATH / "ALGORITHM.md"
    if not alg_file.exists():
        raise FileNotFoundError("Algorithm file not found. Please create vault/data/ALGORITHM.md with the name of the JWT algorithm (e.g. HS256).")
    return alg_file.read_text().strip()


def week_of_year(d: date) -> tuple[int, int]:
    """Return (ISO-year, ISO-week) for the given date."""
    y, w, _ = d.isocalendar()
    return y, w


def parse_date(s: str) -> date:
    """Parse common date formats into a date object.

    Accepted formats: YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY, DD/MM/YYYY
    """
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {s}. Use YYYY-MM-DD or DD-MM-YYYY")


def get_today_file():
    today_str = date.today().isoformat()
    y, w = week_of_year(date.today())
    y = str(y)
    w = str(w)
    return CHORES_PATH / y / w / f"{today_str}.md"


def parse_day(filepath: Path):
    if not filepath.exists():
        return {}

    lines = filepath.read_text().splitlines()

    data = {}
    current_group = None
    task_index = 0

    for line in lines:
        line = line.rstrip()

        # Section header: "- Name"
        if line.startswith("- "):
            current_group = line[2:].strip()
            data[current_group] = []
            task_index = 0
            continue

        # Task line: "1. [x] [[Task]]"
        if line.strip().startswith("1.") or line.strip().startswith("2.") or line.strip().startswith("3."):
            # Match pattern: "1. [x] [[Task]]"
            match = re.match(r"\d+\.\s*\[([ x])]\s*\[\[(.+?)]]", line.strip())
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

    if not file.exists():
        return {"error": "No file for today"}

    lines = file.read_text().splitlines()
    current_group = None
    task_counter = -1

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect section header: "- Name"
        if line.startswith("- "):
            current_group = line[2:].strip()
            task_counter = -1
            continue

        # Detect task lines: "1. [x] [[Task]]"
        match = re.match(r"(\d+\.\s*)\[([ x])](\s*\[\[.+]])", stripped)
        if match and current_group == person:
            task_counter += 1

            if task_counter == task_index:
                prefix = match.group(1)
                current_state = match.group(2)
                rest = match.group(3)

                # Toggle state
                new_state = " " if current_state == "x" else "x"

                lines[i] = f"{prefix}[{new_state}]{rest}"
                break

    file.write_text("\n".join(lines))
    return {"status": "ok"}


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    users = load_users()
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[get_algorithm()])
        name = payload.get("sub")
        if name not in users:
            raise HTTPException(status_code=401)
        return name
    except JWTError:
        raise HTTPException(status_code=401)


if __name__ == "__main__":
    print(get_secret_key())
