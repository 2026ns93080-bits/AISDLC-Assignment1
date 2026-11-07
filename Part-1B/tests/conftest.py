"""Test configuration. Owned by the human engineer; the coding agent must not modify it.

Puts ``src`` (the application) and ``.harness`` (the independent evaluator) on the import path.
No packaging files are needed, and the constitution forbids the agent from creating any.
"""

import sys
from pathlib import Path

PART_ROOT = Path(__file__).resolve().parent.parent

for entry in (PART_ROOT / "src", PART_ROOT / ".harness", Path(__file__).resolve().parent):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))
