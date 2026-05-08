# application/api/deps.py

# Local External Imports
from core.config import USERS_PATH
from file_io.user_io import load_users


# Partial Imports
from fastapi import HTTPException


def get_user_or_404(uuid: str):
    users = load_users()
    user = users.get(uuid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_user_file(uuid: str):
    user = get_user_or_404(uuid)  # Ensure user exists
    return USERS_PATH / f"{user['name']}.md"


def require_admin(uuid: str):
    user = get_user_or_404(uuid)
    permissions = user.get("permissions") or []
    if "admin" not in permissions:
        raise HTTPException(status_code=403, detail="Admin permissions required")
    return user


if __name__ == "__main__":
    print(get_user_or_404("some-uuid"))
