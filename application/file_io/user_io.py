# application/file_io/user_io.py

# Local External Imports
from core.config import USERS_PATH

# Full Imports
import frontmatter


def load_users():
    users = {}
    for file in USERS_PATH.glob("*.md"):
        meta = frontmatter.load(file).metadata
        if not meta:
            continue

        uuid = meta.get("uuid")
        if not uuid:
            continue

        users[uuid] = {
            "name": file.stem,
            "display_name": meta.get("display_name"),
            "permissions": meta.get("permissions"),
            "unavailable_days": meta.get("unavailable_days", []),
            "total_exp": meta.get("total_exp", 0),
        }
    return users


def get_uuid_by_display_name(display_name: str):
    users = load_users()
    for uuid, user in users.items():
        if user.get("display_name") == display_name:
            return uuid
    return None
