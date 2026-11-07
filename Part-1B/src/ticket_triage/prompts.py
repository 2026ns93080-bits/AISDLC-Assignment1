from pathlib import Path

_SYSTEM_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "prompts" / "system.md"
)


def load_system_prompt() -> str:
    return _SYSTEM_PROMPT_PATH.read_bytes().decode("utf-8")
