"""Acceptance tests for the Parking Fee Calculator (Part 1A).

Derived from specs/001-parking-fee-calculator/spec.md: AC-001..AC-043 and SC-003.
Owned by the human engineer; the coding agent must not modify this file.

Every test id carries the acceptance-criterion id it verifies (for example
``test_valid_ticket[AC-015]``), which is how the harness checks that every AC in the
specification has at least one automated test (constitution quality gate).

Expected values are written out literally from the specification. No expected value
is computed with the formula under test.

Most tests call ``parking_fee.cli.main(argv)`` in-process and capture the raw bytes
written to stdout and stderr. A few tests run ``python -m parking_fee`` in a
subprocess to check the real entry point and byte-exact output.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PART_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PART_ROOT / "src"

# Exact error messages from FR-013.
ERR_ARGS = "error: expected exactly one input file path"
ERR_READ = "error: cannot read input file"
ERR_JSON = "error: input must be valid JSON"
ERR_OBJ = "error: input must be a JSON object"
ERR_ENTRY = "error: entry must be a timestamp in YYYY-MM-DD HH:MM format"
ERR_EXIT = "error: exit must be a timestamp in YYYY-MM-DD HH:MM format"
ERR_VEHICLE = "error: vehicle_type must be one of: two_wheeler, car"
ERR_LOST = "error: lost_ticket must be true or false"
ERR_ORDER = "error: exit must not be earlier than entry"


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------


def ticket(entry, exit_, vehicle_type, **extra):
    """Return compact UTF-8 JSON bytes for a ticket (keys in the order used by the spec)."""
    body = {"entry": entry, "exit": exit_, "vehicle_type": vehicle_type}
    body.update(extra)
    return json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def success_line(duration, penalty, fee, total, vehicle):
    """Exact expected stdout bytes for a successful run (FR-012)."""
    text = (
        '{"duration_minutes":%d,"lost_ticket_penalty":%d,"parking_fee":%d,'
        '"total_fee":%d,"vehicle_type":"%s"}\n' % (duration, penalty, fee, total, vehicle)
    )
    return text.encode("utf-8")


def error_line(message):
    """Exact expected stderr bytes for a failed run (FR-013)."""
    return (message + "\n").encode("utf-8")


def run_in_process(argv, capsysbinary):
    """Call the CLI entry function and return (exit code, stdout bytes, stderr bytes)."""
    from parking_fee.cli import main  # imported lazily so tests are collectable before src exists

    try:
        code = main(list(argv))
    except SystemExit as exc:
        code = exc.code
    out, err = capsysbinary.readouterr()
    return code, out, err


def run_subprocess(argv, cwd):
    """Run ``python -m parking_fee`` and return (exit code, stdout bytes, stderr bytes)."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC_DIR)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    done = subprocess.run(  # noqa: S603 - fixed interpreter, test-only
        [sys.executable, "-m", "parking_fee", *argv],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        timeout=60,
        check=False,
    )
    return done.returncode, done.stdout, done.stderr


def check(label, observed, want_code, want_out, want_err):
    """Compare exit status, stdout and stderr; raise one message with expected and observed."""
    __tracebackhide__ = True
    code, out, err = observed
    lines = []
    if code != want_code:
        lines.append(f"  exit status: expected {want_code!r}, observed {code!r}")
    if out != want_out:
        lines.append(f"  stdout: expected {want_out!r}, observed {out!r}")
    if err != want_err:
        lines.append(f"  stderr: expected {want_err!r}, observed {err!r}")
    if lines:
        raise AssertionError(label + "\n" + "\n".join(lines))


def materialise(vector, tmp_path):
    """Create the files a vector needs and return its argument list."""
    _ac, content, args, _message, make_dir = vector
    ticket_path = tmp_path / "ticket.json"
    if content is not None:
        ticket_path.write_bytes(content)
    if make_dir:
        (tmp_path / "directory").mkdir()
    return [a.replace("{ticket}", str(ticket_path)).replace("{tmp}", str(tmp_path)) for a in args]


# --------------------------------------------------------------------------------------
# Valid tickets: AC-001..AC-023 and AC-034..AC-039
# (id, entry, exit, vehicle, extra keys, duration, lost-ticket penalty, parking fee, total)
# --------------------------------------------------------------------------------------

CAR = "car"
TWO = "two_wheeler"

VALID_CASES = [
    ("AC-001", "2026-01-01 10:00", "2026-01-01 10:00", CAR, {}, 0, 0, 0, 0),
    ("AC-002", "2026-01-01 10:00", "2026-01-01 10:00", TWO, {}, 0, 0, 0, 0),
    ("AC-003", "2026-01-01 10:00", "2026-01-01 10:15", CAR, {}, 15, 0, 0, 0),
    ("AC-004", "2026-01-01 10:00", "2026-01-01 10:15", TWO, {}, 15, 0, 0, 0),
    ("AC-005", "2026-01-01 10:00", "2026-01-01 10:16", CAR, {}, 16, 0, 40, 40),
    ("AC-006", "2026-01-01 10:00", "2026-01-01 10:16", TWO, {}, 16, 0, 20, 20),
    ("AC-007", "2026-01-01 10:00", "2026-01-01 11:00", CAR, {}, 60, 0, 40, 40),
    ("AC-008", "2026-01-01 10:00", "2026-01-01 11:00", TWO, {}, 60, 0, 20, 20),
    ("AC-009", "2026-01-01 10:00", "2026-01-01 11:01", CAR, {}, 61, 0, 80, 80),
    ("AC-010", "2026-01-01 10:00", "2026-01-01 11:01", TWO, {}, 61, 0, 40, 40),
    ("AC-011", "2026-01-01 10:00", "2026-01-02 10:00", CAR, {}, 1440, 0, 300, 300),
    ("AC-012", "2026-01-01 10:00", "2026-01-02 10:00", TWO, {}, 1440, 0, 150, 150),
    ("AC-013", "2026-01-01 10:00", "2026-01-02 10:01", CAR, {}, 1441, 0, 340, 340),
    ("AC-014", "2026-01-01 10:00", "2026-01-02 10:01", TWO, {}, 1441, 0, 170, 170),
    ("AC-015", "2026-01-01 10:00", "2026-01-01 13:10", CAR, {}, 190, 0, 160, 160),
    ("AC-016", "2026-01-01 10:00", "2026-01-01 13:10", TWO, {}, 190, 0, 80, 80),
    ("AC-017", "2026-01-01 10:00", "2026-01-02 10:15", CAR, {}, 1455, 0, 340, 340),
    ("AC-018", "2026-01-01 10:00", "2026-01-02 19:20", CAR, {}, 2000, 0, 600, 600),
    ("AC-019", "2026-01-01 10:00", "2026-01-02 19:20", TWO, {}, 2000, 0, 300, 300),
    ("AC-020", "2026-01-01 10:00", "2026-01-01 10:00", CAR, {"lost_ticket": True}, 0, 200, 0, 200),
    ("AC-021", "2026-01-01 10:00", "2026-01-01 11:01", TWO, {"lost_ticket": True}, 61, 200, 40, 240),
    ("AC-022", "2026-01-01 10:00", "2026-01-01 10:16", CAR, {"lost_ticket": False}, 16, 0, 40, 40),
    ("AC-023", "2026-01-01 10:00", "2026-01-01 10:16", CAR, {"reference": "ignored"}, 16, 0, 40, 40),
    ("AC-034", "2026-01-01 10:00", "2026-01-01 17:00", CAR, {}, 420, 0, 280, 280),
    ("AC-035", "2026-01-01 10:00", "2026-01-01 17:01", CAR, {}, 421, 0, 300, 300),
    ("AC-036", "2026-01-01 10:00", "2026-01-01 17:00", TWO, {}, 420, 0, 140, 140),
    ("AC-037", "2026-01-01 10:00", "2026-01-01 17:01", TWO, {}, 421, 0, 150, 150),
    ("AC-038", "2026-12-31 23:50", "2027-01-01 00:10", CAR, {}, 20, 0, 40, 40),
    ("AC-039", "2028-02-28 12:00", "2028-03-01 12:00", CAR, {}, 2880, 0, 600, 600),
]

VALID_IDS = [case[0] for case in VALID_CASES]


@pytest.mark.parametrize(
    ("ac", "entry", "exit_", "vehicle", "extra", "duration", "penalty", "fee", "total"),
    VALID_CASES,
    ids=VALID_IDS,
)
def test_valid_ticket(
    ac, entry, exit_, vehicle, extra, duration, penalty, fee, total, tmp_path, monkeypatch, capsysbinary
):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "ticket.json"
    path.write_bytes(ticket(entry, exit_, vehicle, **extra))
    observed = run_in_process([str(path)], capsysbinary)
    check(ac, observed, 0, success_line(duration, penalty, fee, total, vehicle), b"")


# --------------------------------------------------------------------------------------
# Invalid input: AC-024..AC-033 and AC-040..AC-043
# (id, file bytes or None, argument template, expected stderr message, create directory?)
# "{ticket}" is the path of ticket.json and "{tmp}" the temporary directory.
# --------------------------------------------------------------------------------------

VALID_EXIT = "2026-01-01 11:00"
VALID_ENTRY = "2026-01-01 10:00"


def raw(text):
    return text.encode("utf-8")


ERROR_VECTORS = [
    # AC-024: argument count
    ("AC-024a", None, [], ERR_ARGS, False),
    ("AC-024b", None, ["{tmp}/missing-a.json", "{tmp}/missing-b.json"], ERR_ARGS, False),
    # AC-025: missing path, directory
    ("AC-025a", None, ["{tmp}/missing.json"], ERR_READ, False),
    ("AC-025b", None, ["{tmp}/directory"], ERR_READ, True),
    # AC-026: invalid JSON
    ("AC-026a", b"", ["{ticket}"], ERR_JSON, False),
    ("AC-026b", b"\xff", ["{ticket}"], ERR_JSON, False),
    ("AC-026c", b"{[", ["{ticket}"], ERR_JSON, False),
    (
        "AC-026d",
        raw(
            '{"entry":"2026-01-01 10:00","entry":"2026-01-01 11:00",'
            '"exit":"2026-01-01 12:00","vehicle_type":"car"}'
        ),
        ["{ticket}"],
        ERR_JSON,
        False,
    ),
    # AC-027: valid JSON that is not an object
    ("AC-027a", b"[]", ["{ticket}"], ERR_OBJ, False),
    ("AC-027b", b"null", ["{ticket}"], ERR_OBJ, False),
    ("AC-027c", b'"ticket"', ["{ticket}"], ERR_OBJ, False),
    # AC-028: entry
    ("AC-028a", raw('{"exit":"2026-01-01 11:00","vehicle_type":"car"}'), ["{ticket}"], ERR_ENTRY, False),
    (
        "AC-028b",
        raw('{"entry":1,"exit":"2026-01-01 11:00","vehicle_type":"car"}'),
        ["{ticket}"],
        ERR_ENTRY,
        False,
    ),
    (
        "AC-028c",
        raw('{"entry":"2026-1-01 10:00","exit":"2026-01-01 11:00","vehicle_type":"car"}'),
        ["{ticket}"],
        ERR_ENTRY,
        False,
    ),
    (
        "AC-028d",
        raw('{"entry":"2026-02-29 10:00","exit":"2026-03-01 10:00","vehicle_type":"car"}'),
        ["{ticket}"],
        ERR_ENTRY,
        False,
    ),
    (
        "AC-028e",
        raw('{"entry":"2026-01-01 24:00","exit":"2026-01-02 10:00","vehicle_type":"car"}'),
        ["{ticket}"],
        ERR_ENTRY,
        False,
    ),
    # AC-029: exit
    ("AC-029a", raw('{"entry":"2026-01-01 10:00","vehicle_type":"car"}'), ["{ticket}"], ERR_EXIT, False),
    (
        "AC-029b",
        raw('{"entry":"2026-01-01 10:00","exit":null,"vehicle_type":"car"}'),
        ["{ticket}"],
        ERR_EXIT,
        False,
    ),
    (
        "AC-029c",
        raw('{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00:00","vehicle_type":"car"}'),
        ["{ticket}"],
        ERR_EXIT,
        False,
    ),
    (
        "AC-029d",
        raw('{"entry":"2026-04-30 10:00","exit":"2026-04-31 10:00","vehicle_type":"car"}'),
        ["{ticket}"],
        ERR_EXIT,
        False,
    ),
    # AC-030: vehicle_type
    (
        "AC-030a",
        raw('{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00"}'),
        ["{ticket}"],
        ERR_VEHICLE,
        False,
    ),
    (
        "AC-030b",
        raw('{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00","vehicle_type":1}'),
        ["{ticket}"],
        ERR_VEHICLE,
        False,
    ),
    (
        "AC-030c",
        raw('{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00","vehicle_type":"Car"}'),
        ["{ticket}"],
        ERR_VEHICLE,
        False,
    ),
    # AC-031: lost_ticket
    (
        "AC-031a",
        raw('{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00","vehicle_type":"car","lost_ticket":null}'),
        ["{ticket}"],
        ERR_LOST,
        False,
    ),
    (
        "AC-031b",
        raw(
            '{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00",'
            '"vehicle_type":"car","lost_ticket":"true"}'
        ),
        ["{ticket}"],
        ERR_LOST,
        False,
    ),
    # AC-032: exit before entry
    (
        "AC-032",
        raw(
            '{"entry":"2026-01-01 11:00","exit":"2026-01-01 10:59",'
            '"vehicle_type":"car","lost_ticket":false}'
        ),
        ["{ticket}"],
        ERR_ORDER,
        False,
    ),
    # AC-033: validation precedence vectors (a) to (i)
    ("AC-033a", None, ["{tmp}/missing-a.json", "{tmp}/missing-b.json"], ERR_ARGS, False),
    ("AC-033b", None, ["{tmp}/missing.json"], ERR_READ, False),
    ("AC-033c", b"{[", ["{ticket}"], ERR_JSON, False),
    ("AC-033d", b"[]", ["{ticket}"], ERR_OBJ, False),
    (
        "AC-033e",
        raw('{"entry":"bad","exit":"bad","vehicle_type":"unknown","lost_ticket":null}'),
        ["{ticket}"],
        ERR_ENTRY,
        False,
    ),
    (
        "AC-033f",
        raw('{"entry":"2026-01-01 10:00","exit":"bad","vehicle_type":"unknown","lost_ticket":null}'),
        ["{ticket}"],
        ERR_EXIT,
        False,
    ),
    (
        "AC-033g",
        raw(
            '{"entry":"2026-01-01 11:00","exit":"2026-01-01 10:59",'
            '"vehicle_type":"unknown","lost_ticket":null}'
        ),
        ["{ticket}"],
        ERR_VEHICLE,
        False,
    ),
    (
        "AC-033h",
        raw(
            '{"entry":"2026-01-01 11:00","exit":"2026-01-01 10:59",'
            '"vehicle_type":"car","lost_ticket":null}'
        ),
        ["{ticket}"],
        ERR_LOST,
        False,
    ),
    (
        "AC-033i",
        raw(
            '{"entry":"2026-01-01 11:00","exit":"2026-01-01 10:59",'
            '"vehicle_type":"car","lost_ticket":false}'
        ),
        ["{ticket}"],
        ERR_ORDER,
        False,
    ),
    # AC-040: a sole "--help" argument is a path, not an option (no such file exists)
    ("AC-040", None, ["--help"], ERR_READ, False),
    # AC-041: fullwidth digits are not ASCII digits
    (
        "AC-041",
        raw('{"entry":"２０２６-０１-０１ １０:００","exit":"2026-01-01 11:00","vehicle_type":"car"}'),
        ["{ticket}"],
        ERR_ENTRY,
        False,
    ),
    # AC-042: a UTF-8 byte-order mark makes the file invalid JSON
    (
        "AC-042",
        b"\xef\xbb\xbf" + ticket(VALID_ENTRY, VALID_EXIT, CAR),
        ["{ticket}"],
        ERR_JSON,
        False,
    ),
    # AC-043: duplicate keys are rejected at any nesting depth
    (
        "AC-043",
        raw(
            '{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00",'
            '"vehicle_type":"car","extra":{"a":1,"a":2}}'
        ),
        ["{ticket}"],
        ERR_JSON,
        False,
    ),
]

ERROR_IDS = [vector[0] for vector in ERROR_VECTORS]


@pytest.mark.parametrize("vector", ERROR_VECTORS, ids=ERROR_IDS)
def test_invalid_input(vector, tmp_path, monkeypatch, capsysbinary):
    monkeypatch.chdir(tmp_path)
    argv = materialise(vector, tmp_path)
    observed = run_in_process(argv, capsysbinary)
    check(vector[0], observed, 2, b"", error_line(vector[3]))


# --------------------------------------------------------------------------------------
# End-to-end through the real entry point: python -m parking_fee (byte-exact, LF only)
# --------------------------------------------------------------------------------------

END_TO_END_VALID = ["AC-015", "AC-021", "AC-039"]
END_TO_END_INVALID = ["AC-024a", "AC-025a", "AC-040", "AC-042", "AC-043"]


@pytest.mark.parametrize("case", [c for c in VALID_CASES if c[0] in END_TO_END_VALID], ids=END_TO_END_VALID)
def test_valid_ticket_end_to_end(case, tmp_path):
    ac, entry, exit_, vehicle, extra, duration, penalty, fee, total = case
    path = tmp_path / "ticket.json"
    path.write_bytes(ticket(entry, exit_, vehicle, **extra))
    observed = run_subprocess([str(path)], tmp_path)
    check(ac + " (python -m parking_fee)", observed, 0, success_line(duration, penalty, fee, total, vehicle), b"")


@pytest.mark.parametrize(
    "vector", [v for v in ERROR_VECTORS if v[0] in END_TO_END_INVALID], ids=END_TO_END_INVALID
)
def test_invalid_input_end_to_end(vector, tmp_path):
    argv = materialise(vector, tmp_path)
    observed = run_subprocess(argv, tmp_path)
    check(vector[0] + " (python -m parking_fee)", observed, 2, b"", error_line(vector[3]))


# --------------------------------------------------------------------------------------
# SC-003 / NFR-001: repeating an identical invocation gives identical bytes and status
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ac", "entry", "exit_", "vehicle", "extra", "duration", "penalty", "fee", "total"),
    VALID_CASES,
    ids=VALID_IDS,
)
def test_sc003_repeat_valid(
    ac, entry, exit_, vehicle, extra, duration, penalty, fee, total, tmp_path, monkeypatch, capsysbinary
):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "ticket.json"
    path.write_bytes(ticket(entry, exit_, vehicle, **extra))
    first = run_in_process([str(path)], capsysbinary)
    second = run_in_process([str(path)], capsysbinary)
    assert first == second, f"{ac} SC-003: repeated run differs: first {first!r}, second {second!r}"
    assert first[1], f"{ac} SC-003: no output produced"


@pytest.mark.parametrize("vector", ERROR_VECTORS, ids=ERROR_IDS)
def test_sc003_repeat_invalid(vector, tmp_path, monkeypatch, capsysbinary):
    monkeypatch.chdir(tmp_path)
    argv = materialise(vector, tmp_path)
    first = run_in_process(argv, capsysbinary)
    second = run_in_process(argv, capsysbinary)
    assert first == second, f"{vector[0]} SC-003: repeated run differs: first {first!r}, second {second!r}"
    assert first[2], f"{vector[0]} SC-003: no error line produced"


def test_sc003_repeat_end_to_end(tmp_path):
    path = tmp_path / "ticket.json"
    path.write_bytes(ticket("2026-01-01 10:00", "2026-01-01 13:10", CAR))
    want = success_line(190, 0, 160, 160, CAR)
    first = run_subprocess([str(path)], tmp_path)
    second = run_subprocess([str(path)], tmp_path)
    check("AC-015 SC-003 first run (python -m parking_fee)", first, 0, want, b"")
    check("AC-015 SC-003 second run (python -m parking_fee)", second, 0, want, b"")
    assert first == second, f"AC-015 SC-003: repeated process run differs: {first!r} vs {second!r}"
