# application/services/user_service.py


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
