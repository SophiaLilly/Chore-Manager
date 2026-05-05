# application/util/task_parsing.py

# Partial Imports
from re import compile


TASK_PATTERN = compile(r"\d+\.\s*\[([ x])]\s*\[\[(.+?)]]")
TOGGLE_PATTERN = compile(r"(\d+\.\s*)\[([ x])](\s*\[\[.+]])")
