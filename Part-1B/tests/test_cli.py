"""Command-line tests. Human-owned.

Derived from specs/001-support-ticket-triage/spec.md (AC-022..AC-029, AC-044, AC-045, AC-055,
FR-012, FR-013). ``main(argv, client)`` is called in-process with a fake model and the raw bytes
written to stdout and stderr are captured. A few tests run ``python -m ticket_triage`` in a
subprocess for flows that never reach the model. Test ids carry the acceptance-criterion id.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from helpers import (
    C,
    R,
    T,
    FakeClient,
    fake_openai_module,
    forbid_openai_client,
    http_library,
    install_openai_factory,
    with_summary,
)

PART_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PART_ROOT / "src"

BILLING_TICKET = "My card was charged twice; please refund one charge."
T_LINE = (
    '{"action":"triage","category":"billing","clarification_question":null,'
    '"priority":"medium","refusal_reason":null,"summary":"Refund request for duplicate charge."}'
)
C_LINE = (
    '{"action":"clarify","category":null,"clarification_question":"What problem are you experiencing?",'
    '"priority":null,"refusal_reason":null,"summary":null}'
)
R_LINE = (
    '{"action":"refuse","category":null,"clarification_question":null,"priority":null,'
    '"refusal_reason":"not_a_support_ticket","summary":null}'
)
INVALID_INPUT_LINE = (
    '{"action":"refuse","category":null,"clarification_question":null,"priority":null,'
    '"refusal_reason":"invalid_input","summary":null}'
)

ERR_ARGS = "error: expected exactly one input file path"
ERR_READ = "error: cannot read input file"
ERR_SERVICE = "error: model service unavailable"
ERR_INVALID = "error: model returned an invalid response"


def run_main(argv, client, capsysbinary):
    from ticket_triage.cli import main

    try:
        code = main(list(argv), client)
    except SystemExit as exc:
        code = exc.code
    out, err = capsysbinary.readouterr()
    return code, out, err


def line(text):
    return text.encode("utf-8") + b"\n"


def ticket_file(tmp_path, content):
    path = tmp_path / "ticket.txt"
    path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
    return str(path)


def check(label, observed, code, out, err):
    __tracebackhide__ = True
    got_code, got_out, got_err = observed
    problems = []
    if got_code != code:
        problems.append(f"  exit status: expected {code!r}, observed {got_code!r}")
    if got_out != out:
        problems.append(f"  stdout: expected {out!r}, observed {got_out!r}")
    if got_err != err:
        problems.append(f"  stderr: expected {err!r}, observed {got_err!r}")
    if problems:
        raise AssertionError(label + "\n" + "\n".join(problems))


# --------------------------------------------------------------------------------------
# Successful decisions (AC-022..AC-025, AC-044, AC-045, AC-055)
# --------------------------------------------------------------------------------------


def test_ac022_triage_decision(tmp_path, capsysbinary):
    client = FakeClient(reply=T)
    observed = run_main([ticket_file(tmp_path, BILLING_TICKET)], client, capsysbinary)
    check("AC-022", observed, 0, line(T_LINE), b"")


def test_ac023_clarify_decision(tmp_path, capsysbinary):
    observed = run_main([ticket_file(tmp_path, "I need help with something.")], FakeClient(reply=C), capsysbinary)
    check("AC-023", observed, 0, line(C_LINE), b"")


def test_ac024_refuse_decision(tmp_path, capsysbinary):
    observed = run_main([ticket_file(tmp_path, "Write a poem about the moon.")], FakeClient(reply=R), capsysbinary)
    check("AC-024", observed, 0, line(R_LINE), b"")


def test_ac025_empty_file_gives_invalid_input_decision(tmp_path, capsysbinary):
    client = FakeClient(reply=T)
    observed = run_main([ticket_file(tmp_path, b"")], client, capsysbinary)
    check("AC-025", observed, 0, line(INVALID_INPUT_LINE), b"")
    assert client.calls == []


def test_ac044_leading_byte_order_mark_is_removed(tmp_path, capsysbinary):
    client = FakeClient(reply=T)
    path = ticket_file(tmp_path, b"\xef\xbb\xbf" + BILLING_TICKET.encode("utf-8"))
    observed = run_main([path], client, capsysbinary)
    check("AC-044", observed, 0, line(T_LINE), b"")
    assert client.calls[0][1] == BILLING_TICKET


def test_ac045_crlf_counts_as_two_characters_with_no_newline_translation(tmp_path, capsysbinary):
    client = FakeClient(reply=T)
    path = ticket_file(tmp_path, b"x" * 3999 + b"\r\n")
    observed = run_main([path], client, capsysbinary)
    check("AC-045", observed, 0, line(INVALID_INPUT_LINE), b"")
    assert client.calls == []


def test_fr012_exactly_4000_characters_in_a_file_reaches_the_model(tmp_path, capsysbinary):
    client = FakeClient(reply=T)
    observed = run_main([ticket_file(tmp_path, b"x" * 4000)], client, capsysbinary)
    check("FR-012 boundary", observed, 0, line(T_LINE), b"")
    assert len(client.calls) == 1


def test_ac055_non_ascii_output_is_utf8_bytes_with_one_lf(tmp_path, capsysbinary):
    reply = with_summary("R\u00e9sum\u00e9 of the billing issue")
    expected = (
        b'{"action":"triage","category":"billing","clarification_question":null,'
        b'"priority":"medium","refusal_reason":null,"summary":"R\xc3\xa9sum\xc3\xa9 of the billing issue"}\n'
    )
    observed = run_main([ticket_file(tmp_path, BILLING_TICKET)], FakeClient(reply=reply), capsysbinary)
    check("AC-055", observed, 0, expected, b"")
    out = observed[1]
    assert b"\\u" not in out and b"\r" not in out and not out.startswith(b"\xef\xbb\xbf")
    assert out.endswith(b"\n") and not out.endswith(b"\n\n")


def test_fr012_output_has_alphabetical_keys(tmp_path, capsysbinary):
    _code, out, _err = run_main([ticket_file(tmp_path, BILLING_TICKET)], FakeClient(reply=T), capsysbinary)
    import json

    keys = list(json.loads(out.decode("utf-8")))
    assert keys == sorted(keys)


# --------------------------------------------------------------------------------------
# Failures (AC-026..AC-029)
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("argv", [[], ["one", "two"]], ids=["AC-026-zero", "AC-026-two"])
def test_ac026_wrong_argument_count(argv, capsysbinary):
    client = FakeClient(reply=T)
    check("AC-026", run_main(argv, client, capsysbinary), 2, b"", line(ERR_ARGS))
    assert client.calls == []


def test_fr012_option_looking_argument_is_a_path_not_an_option(tmp_path, monkeypatch, capsysbinary):
    monkeypatch.chdir(tmp_path)
    check("FR-012 option", run_main(["--help"], FakeClient(reply=T), capsysbinary), 2, b"", line(ERR_READ))


def make_unreadable(tmp_path, kind):
    if kind == "missing":
        return str(tmp_path / "does-not-exist.txt")
    if kind == "directory":
        folder = tmp_path / "folder"
        folder.mkdir()
        return str(folder)
    return ticket_file(tmp_path, b"\xff")


@pytest.mark.parametrize("kind", ["missing", "directory", "invalid-utf8"], ids=["AC-027-missing", "AC-027-directory", "AC-027-0xFF"])
def test_ac027_unreadable_input(kind, tmp_path, capsysbinary):
    client = FakeClient(reply=T)
    check("AC-027", run_main([make_unreadable(tmp_path, kind)], client, capsysbinary), 2, b"", line(ERR_READ))
    assert client.calls == []


def test_ac028_service_unavailable_exits_3(tmp_path, monkeypatch, capsysbinary):
    import openai
    from ticket_triage.openai_client import OpenAIClient

    http = http_library()
    request = http.Request("POST", "https://api.openai.com/v1/chat/completions")
    failure = openai.AuthenticationError("hidden detail", response=http.Response(401, request=request), body=None)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-sentinel-0123456789")
    monkeypatch.setenv("OPENAI_MODEL", "test-model-name")
    install_openai_factory(monkeypatch, fake_openai_module(error=failure))
    observed = run_main([ticket_file(tmp_path, BILLING_TICKET)], OpenAIClient(), capsysbinary)
    check("AC-028", observed, 3, b"", line(ERR_SERVICE))
    assert b"hidden detail" not in observed[2] and b"sentinel" not in observed[2]


def test_ac028_missing_configuration_also_exits_3(tmp_path, monkeypatch, capsysbinary):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    forbid_openai_client(monkeypatch)
    check("AC-028 config", run_main([ticket_file(tmp_path, BILLING_TICKET)], None, capsysbinary), 3, b"", line(ERR_SERVICE))


def test_ac029_invalid_reply_exits_4_without_printing_the_reply(tmp_path, capsysbinary):
    secret_reply = "not-json-RAW-REPLY-MARKER"
    observed = run_main([ticket_file(tmp_path, BILLING_TICKET)], FakeClient(reply=secret_reply), capsysbinary)
    check("AC-029", observed, 4, b"", line(ERR_INVALID))
    assert b"RAW-REPLY-MARKER" not in observed[1] + observed[2]


def test_fr013_prohibited_text_in_reply_is_not_printed(tmp_path, capsysbinary):
    reply = with_summary("Card 4111111111111111")
    observed = run_main([ticket_file(tmp_path, BILLING_TICKET)], FakeClient(reply=reply), capsysbinary)
    check("FR-013 card", observed, 4, b"", line(ERR_INVALID))


# --------------------------------------------------------------------------------------
# End to end through the real entry point (flows that never call the model)
# --------------------------------------------------------------------------------------


def run_module(argv, cwd):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC_DIR)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    done = subprocess.run(  # noqa: S603 - fixed interpreter, test-only
        [sys.executable, "-m", "ticket_triage", *argv],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        timeout=60,
        check=False,
    )
    return done.returncode, done.stdout, done.stderr


def test_ac026_end_to_end_without_arguments(tmp_path):
    check("AC-026 (python -m)", run_module([], tmp_path), 2, b"", line(ERR_ARGS))


def test_ac027_end_to_end_missing_file(tmp_path):
    check("AC-027 (python -m)", run_module([str(tmp_path / "nothing.txt")], tmp_path), 2, b"", line(ERR_READ))


def test_ac025_end_to_end_empty_file(tmp_path):
    check("AC-025 (python -m)", run_module([ticket_file(tmp_path, b"")], tmp_path), 0, line(INVALID_INPUT_LINE), b"")


def test_fr012_end_to_end_4001_characters_is_refused_by_the_guard(tmp_path):
    check(
        "FR-012 (python -m)",
        run_module([ticket_file(tmp_path, b"x" * 4001)], tmp_path),
        0,
        line(INVALID_INPUT_LINE),
        b"",
    )
