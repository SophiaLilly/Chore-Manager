# application/file_io/streak_io.py

# Local External Imports
from application.api.deps import get_user_or_404
from application.core.config import USERS_PATH

# Full Imports
import frontmatter


def get_user_streak(uuid: str) -> dict:
    user = get_user_or_404(uuid)
    user_file = USERS_PATH / f"{user["name"]}.md"
    post = frontmatter.load(user_file)
    metadata = post.metadata
    return {
        "current_streak": metadata.get("current_streak", 0),
        "best_streak": metadata.get("best_streak", 0),
        "last_completion_date": metadata.get("last_completion_date", None)
    }


def migrate_users_to_streak_system():
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
    print(get_user_streak(uuid=""))