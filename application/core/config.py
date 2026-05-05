# application/core/config.py

# Partial Imports
from pathlib import Path


BASE_PATH = Path(__file__).resolve().parent.parent.parent
VAULT_PATH = BASE_PATH / "vault"
CHORES_PATH = VAULT_PATH / "chores"
PEOPLE_PATH = VAULT_PATH / "people"
DATA_PATH = VAULT_PATH / "data"
TASKS_PATH = DATA_PATH / "tasks"
USERS_PATH = DATA_PATH / "users"
VARIABLES_PATH = DATA_PATH / "variables"


if __name__ == '__main__':
    print(BASE_PATH)