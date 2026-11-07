import os
import pathlib


def load_env(path: pathlib.Path) -> None:
    try:
        contents = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return

    for line in contents.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if name and name not in os.environ:
            try:
                os.environ[name] = value
            except ValueError:
                continue
