# application/services/exp_service.py

# Local External Imports
from api.deps import get_user_file

# Partial Imports
from filelock import FileLock

# Full Imports
import frontmatter
import pprint
pp = pprint.PrettyPrinter(indent=4)


def calculate_exp_for_task(task: dict) -> int:
    base_exp = task.get("base_exp", 10)
    difficulty = task.get("difficulty", 1)
    return int(base_exp * difficulty)


def get_user_exp(user_uuid: str):
    user_file = get_user_file(user_uuid)

    post = frontmatter.load(user_file)

    return post.metadata.get("total_exp", 0)


def calculate_new_exp(current_exp: int, additional_exp: int) -> int:
    return current_exp + additional_exp


def update_user_exp_for_task(user_uuid: str, task: dict) -> dict:
    user_file = get_user_file(user_uuid)
    with FileLock(str(user_file) + ".lock"):
        post = frontmatter.load(user_file)
        metadata = post.metadata
        pprint.pprint(metadata)

        exp_gained = calculate_exp_for_task(task)
        user_total_exp = get_user_exp(user_uuid)
        new_total_exp = calculate_new_exp(user_total_exp, exp_gained)

        metadata["total_exp"] = new_total_exp
        post.metadata = metadata
        user_file.write_text(frontmatter.dumps(post))

    return {
        "total_exp": new_total_exp,
        "exp_gained": exp_gained,
    }


def deduct_user_exp_for_task(user_uuid: str, task: dict) -> dict:
    user_file = get_user_file(user_uuid)
    with FileLock(str(user_file) + ".lock"):
        post = frontmatter.load(user_file)
        metadata = post.metadata

        exp_deducted = calculate_exp_for_task(task)
        user_total_exp = get_user_exp(user_uuid)
        new_total_exp = max(0, user_total_exp - exp_deducted)  # Don't go below 0

        metadata["total_exp"] = new_total_exp
        post.metadata = metadata
        user_file.write_text(frontmatter.dumps(post))

    return {
        "total_exp": new_total_exp,
        "exp_deducted": exp_deducted,
    }


if __name__ == "__main__":
    #set_user_exp("f4842ac8-e5ef-4029-9bab-7b52cc5b1088", 0)
    pass
