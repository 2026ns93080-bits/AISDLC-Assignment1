"""Test configuration. Owned by the human engineer; the coding agent must not modify it.

Puts ``src`` on the import path so tests can import ``parking_fee`` without
packaging files (the constitution forbids the agent from creating any).
"""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
