"""Entry point and .env loader tests. Human-owned.

Derived from the plan (contracts/interfaces.md, "Executable entry point and configuration"):
``env_loader.load_env(path)`` sets only names that are not already set, and ``__main__`` loads
``<Part-1B root>/.env`` and then runs ``cli.main``. These tests never read or write the real
``.env``: the loader is exercised on temporary files and the entry point is run in-process with
the loader replaced by a recorder.
"""

import runpy
import sys
from pathlib import Path

import pytest

PART_ROOT = Path(__file__).resolve().parent.parent
NAMES = ("TT_TEST_ALPHA", "TT_TEST_BETA", "TT_TEST_GAMMA", "TT_TEST_DELTA")


@pytest.fixture
def clean_names(monkeypatch):
    for name in NAMES:
        monkeypatch.delenv(name, raising=False)


def write_env(tmp_path, text):
    path = tmp_path / ".env"
    path.write_text(text, encoding="utf-8")
    return path


def test_plan_load_env_sets_names_that_are_not_set(tmp_path, clean_names):
    from ticket_triage.env_loader import load_env

    import os

    load_env(write_env(tmp_path, "TT_TEST_ALPHA=one\nTT_TEST_BETA=two\n"))
    assert os.environ["TT_TEST_ALPHA"] == "one"
    assert os.environ["TT_TEST_BETA"] == "two"


def test_plan_load_env_never_overrides_an_existing_value(tmp_path, clean_names, monkeypatch):
    from ticket_triage.env_loader import load_env

    import os

    monkeypatch.setenv("TT_TEST_ALPHA", "already-set")
    load_env(write_env(tmp_path, "TT_TEST_ALPHA=from-file\nTT_TEST_BETA=two\n"))
    assert os.environ["TT_TEST_ALPHA"] == "already-set"
    assert os.environ["TT_TEST_BETA"] == "two"


def test_plan_load_env_ignores_comments_blank_lines_and_malformed_lines(tmp_path, clean_names):
    from ticket_triage.env_loader import load_env

    import os

    text = "# a comment\n\n   \nNOT A KEY VALUE LINE\nTT_TEST_GAMMA=three\n"
    load_env(write_env(tmp_path, text))
    assert os.environ["TT_TEST_GAMMA"] == "three"
    assert "NOT A KEY VALUE LINE" not in os.environ


def test_plan_load_env_strips_spaces_around_names_and_values(tmp_path, clean_names):
    from ticket_triage.env_loader import load_env

    import os

    load_env(write_env(tmp_path, "  TT_TEST_DELTA  =  four  \n"))
    assert os.environ["TT_TEST_DELTA"] == "four"


def test_plan_load_env_missing_file_is_not_an_error(tmp_path):
    from ticket_triage.env_loader import load_env

    load_env(tmp_path / "no-such.env")


def test_plan_load_env_never_prints_values(tmp_path, clean_names, capsys):
    from ticket_triage.env_loader import load_env

    load_env(write_env(tmp_path, "TT_TEST_ALPHA=very-secret-value\n"))
    captured = capsys.readouterr()
    assert "very-secret-value" not in captured.out + captured.err


@pytest.fixture
def recorded_loader(monkeypatch):
    """Replace load_env with a recorder so the real .env is never read."""
    import ticket_triage.env_loader as loader

    calls = []
    monkeypatch.setattr(loader, "load_env", lambda path: calls.append(Path(path)))
    return calls


def run_entry_point(monkeypatch, *arguments):
    monkeypatch.setattr(sys, "argv", ["ticket_triage", *arguments])
    with pytest.raises(SystemExit) as caught:
        runpy.run_module("ticket_triage.__main__", run_name="__main__")
    return caught.value.code


def test_plan_entry_point_loads_dot_env_from_the_part_root(monkeypatch, recorded_loader, capsysbinary):
    code = run_entry_point(monkeypatch)
    assert code == 2
    assert len(recorded_loader) == 1
    assert recorded_loader[0].resolve() == (PART_ROOT / ".env").resolve()


def test_ac026_entry_point_exits_with_the_status_returned_by_main(monkeypatch, recorded_loader, capsysbinary):
    code = run_entry_point(monkeypatch)
    out, err = capsysbinary.readouterr()
    assert (code, out, err) == (2, b"", b"error: expected exactly one input file path\n")


def test_ac025_entry_point_runs_a_whole_decision(monkeypatch, recorded_loader, tmp_path, capsysbinary):
    empty = tmp_path / "empty.txt"
    empty.write_bytes(b"")
    code = run_entry_point(monkeypatch, str(empty))
    out, err = capsysbinary.readouterr()
    expected = (
        b'{"action":"refuse","category":null,"clarification_question":null,"priority":null,'
        b'"refusal_reason":"invalid_input","summary":null}\n'
    )
    assert (code, out, err) == (0, expected, b"")
