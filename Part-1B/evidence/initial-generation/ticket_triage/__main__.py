import sys
from pathlib import Path

from .cli import main
from .env_loader import load_env

load_env(Path(__file__).resolve().parents[2] / ".env")
raise SystemExit(main(sys.argv[1:]))
