# Quickstart: Parking Fee Calculator

## Prerequisites

- Python 3.12 or later.
- A prepared UTF-8 JSON ticket file. See [the command-line contract](./contracts/command-line.md) for all input and output rules.
- The human-owned test and harness environment for the project quality gates. This guide does not create or modify `tests/` or `.harness/`.

No runtime package installation is required; the application uses only the Python standard library.

## Run a valid ticket

From the `Part-1A` project root in PowerShell, put `src` on the import path and invoke the module with exactly one ticket path:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
python -m parking_fee .\ticket.json
```

For the AC-015 example ticket (`entry` at `2026-01-01 10:00`, `exit` at `2026-01-01 13:10`, `vehicle_type` equal to `car`), expected stdout is exactly:

```text
{"duration_minutes":190,"lost_ticket_penalty":0,"parking_fee":160,"total_fee":160,"vehicle_type":"car"}
```

The line ends with one LF; the exit status is `0` and stderr is empty. Other exact cases are listed in the approved specification and traced in [plan.md](./plan.md).

## Check an error case

Using a path that does not exist:

```powershell
python -m parking_fee .\missing.json
```

Expected behavior: exit status `2`, no stdout, and exactly `error: cannot read input file` plus one LF on stderr. A lone `--help` argument is treated as a path and has this same file-read behavior when no such file exists (AC-025, AC-040).

## Validate

Run the human-owned automated tests in the configured development environment:

```powershell
python -m pytest
```

Then run the independent `.harness/` gates using their prescribed invocation. Acceptance tests must compare stdout/stderr bytes, final LF, and exit status; the harness must also enforce Ruff, Bandit, and at least 90% line coverage of `src/` (constitution). No test/harness files or configuration are supplied by this plan.
