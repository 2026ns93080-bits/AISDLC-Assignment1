# Implementation Plan: Parking Fee Calculator

**Branch**: `001-parking-fee-calculator` | **Date**: 2026-10-31 | **Spec**: [spec.md](./spec.md)

**Input**: Approved feature specification in `specs/001-parking-fee-calculator/spec.md`.

## Summary

Build a deterministic Python 3.12+ command-line program that reads one parking ticket from a supplied JSON file and emits either the exact fee result or the first applicable FR-013 error. Separate strict file/JSON/ticket parsing, tariff data, pure integer fee calculation, and command-line handling. The implementation uses only the Python standard library at runtime and writes exact UTF-8 output bytes with LF line endings. This satisfies FR-001–FR-013, NFR-001–NFR-003, and the acceptance cases AC-001–AC-043.

## Technical Context

**Language/Version**: Python 3.12 or later.

**Primary Dependencies**: Python standard library only at runtime (`json`, `re`, `datetime.date`, `os`/`stat`, and `sys` as needed). Development validation tools are owned by the independent harness; no runtime or development dependency manifest is planned.

**Storage**: No persistent storage. Read only the single input path supplied by the caller (FR-001–FR-003).

**Testing**: Human-owned `tests/` and `.harness/`; acceptance-case-to-module/test-file traceability is provided below. Do not create or modify either directory. The constitution's independent gates remain authoritative: tests pass, at least 90% line coverage of `src/`, Ruff has zero errors, and Bandit has no medium/high findings.

**Target Platform**: Python 3.12+ command line, including Windows. Binary standard streams make LF output independent of Windows text newline translation (FR-012, FR-013; NFR-001).

**Project Type**: Command-line application invoked as `python -m parking_fee <path>` with `src` on the import path (FR-001, FR-012, AC-024, AC-040).

**Performance Goals**: No throughput or latency goal is specified; process a single ticket as scoped in the specification.

**Constraints**:
- Keep application code within `src/`; use no runtime dependency other than the standard library.
- Use a single immutable tariff mapping keyed by vehicle type and keep tariff data separate from calculation logic (FR-007; AC-005–AC-022, AC-034–AC-039).
- Use integer minutes and whole-rupee integers only. Convert each validated timestamp to `date(y, m, d).toordinal() * 1440 + hour * 60 + minute`; duration is the plain integer difference. Never use `timedelta.total_seconds()` or floating-point arithmetic (FR-005–FR-010; NFR-002; AC-001–AC-022, AC-038–AC-039).
- Validate timestamps with an explicit `[0-9]` pattern and exact 16-character length; do not use `\d` or `str.isdigit()`. Validate calendar dates with `date` and explicitly bound hours and minutes (FR-005; AC-028, AC-029, AC-041).
- Read with `open(path, "rb")`; non-regular files and any `OSError` are file-read failures. Reject empty bytes and a leading UTF-8 BOM, decode strict UTF-8, and use `json.loads` hooks to reject duplicate object keys and `NaN`/`Infinity`/`-Infinity` (FR-002–FR-003; AC-025–AC-027, AC-042).
- Check only `len(argv)` for argument count; do not use `argparse` or another option parser. A sole `--help` is a path (FR-001; AC-024, AC-040).
- Preserve FR-013 validation precedence and messages. Handle only expected error classes at their boundary; do not use a blanket `except`.
- Write result and error lines through `sys.stdout.buffer` and `sys.stderr.buffer`, respectively, each with exactly one LF. Use `json.dumps(result, sort_keys=True, separators=(",", ":"))` (FR-012–FR-013; NFR-001, NFR-003).

**Scale/Scope**: One ticket per process; only `two_wheeler` and `car`; no persistence, network, time zones, seconds, or additional tariff modes (FR-001, FR-007; AC-001–AC-043).

## Constitution Check

| Principle / constraint | Plan decision and specification trace | Gate |
|---|---|---|
| I. Modular Separation of Concerns | `parsing.py` owns file/JSON reading and validation; `tariff.py` owns tariff data; `calculator.py` is pure; `cli.py` owns argument handling and output; `__main__.py` provides module entry (FR-001–FR-013; AC-001–AC-043). | Pass |
| II. Data-Driven Tariff | One immutable vehicle-keyed tariff structure contains the grace minutes, started-hour rate, 1440-minute-block cap, and lost-ticket penalty (FR-007; AC-005–AC-022, AC-034–AC-039). | Pass |
| III. Integer Money and Durations | Store rupees and minute values as integers; calculate absolute minute indices and use integer ceiling division `(r + 59) // 60` for remaining minutes (FR-006–FR-011; NFR-002; AC-001–AC-022, AC-034–AC-039). | Pass |
| IV. Deterministic Behavior | No clock, randomness, or network; fixed validation order, sorted compact JSON keys, explicit UTF-8 encoding, and exactly one LF per output line (FR-012–FR-013; NFR-001; AC-001–AC-043). | Pass |
| V. Explicit Input and CLI Contract | Exactly one path argument; explicit validation sequence; one error-message mapping function; exit codes 0/2; no partial output or expected-error stack traces (FR-001–FR-006, FR-012–FR-013; NFR-003; AC-024–AC-033, AC-040–AC-043). | Pass |
| Runtime and security | Python 3.12+ standard library only; read only the supplied file; no `eval`, `exec`, `pickle`, shell execution, or secrets (constitution; FR-001–FR-003). | Pass |
| Quality and boundaries | Keep implementation in `src/`; preserve the independent harness gates and map every AC to its module and verifying test file below. Test and harness directories are references only and remain human-owned (constitution; AC-001–AC-043). | Pass |

**Pre-design gate**: Pass. The approved specification and user-provided constraints resolve the implementation choices; no `NEEDS CLARIFICATION` items remain.

**Post-design gate**: Pass. The module boundaries, data model, command contract, and run guide below preserve all constitution principles. No deviations require complexity justification.

## Architecture and Key Decisions

1. **Keep the CLI contract thin and literal.** `__main__.py` passes `sys.argv[1:]` to `main(argv)`. `main` checks `len(argv)` only, invokes file parsing, calculates one result, and writes the result or one mapped error. A lone option-looking argument is still a path (FR-001, FR-012–FR-013; AC-024, AC-033, AC-040).
2. **Parse in the specified order.** After argument count, require a regular file and read it as bytes; reject empty/BOM-prefixed content; strictly decode UTF-8 and parse JSON with duplicate-key and non-finite-constant rejection; require an object; validate `entry`, `exit`, `vehicle_type`, then `lost_ticket`; finally reject an exit preceding entry. One `error_message` function maps expected failure codes to the exact FR-013 text. Expected file/JSON/validation failures are handled narrowly, with no blanket catch (FR-002–FR-006, FR-013; NFR-003; AC-024–AC-033, AC-040–AC-043).
3. **Normalize timestamps to integer minute indices.** Require exactly 16 ASCII-pattern characters matching the timestamp form, validate month/day with `date(y, m, d)` and hour/minute with explicit bounds, then calculate `date(y, m, d).toordinal() * 1440 + hour * 60 + minute`. The parser returns these indices; the calculator subtracts them. No `timedelta`, float, or locale-dependent parsing is involved (FR-005–FR-006; NFR-002; AC-028–AC-029, AC-038–AC-039, AC-041).
4. **Keep one immutable, data-only tariff source.** `tariff.py` contains a frozen tariff record and an immutable mapping keyed by the two supported vehicle strings. Each value carries grace minutes, rupees per started hour, the cap per 1440-minute block, and lost-ticket penalty, using exactly FR-007's values. Calculation does not embed separate policy constants (FR-007; AC-005–AC-022, AC-034–AC-039).
5. **Keep calculation pure and integer-only.** For duration `D <= 15`, parking fee is zero. Otherwise set `q = D // 1440`, `r = D % 1440`, compute remaining started hours as `(r + 59) // 60`, and calculate `q * cap + min(cap, remaining_hours * rate)`. Add the penalty independently, including for a zero-duration stay. No I/O or tariff mutation occurs in `calculator.py` (FR-008–FR-011; NFR-002; AC-001–AC-022, AC-034–AC-039).
6. **Make output bytes stable across platforms.** Serialize the result with sorted keys and compact separators, encode as UTF-8, and write payload plus `b"\n"` using the standard-stream buffers. Errors use the same byte/newline discipline on stderr; errors leave stdout empty (FR-012–FR-013; NFR-001, NFR-003; AC-001–AC-043).
7. **Avoid unrequested project/tooling files.** No `pyproject.toml`, requirements file, CI configuration, test/harness file, or other non-source file is part of the implementation plan. Only the planning/design artifacts under this feature's `specs/` directory are produced in this planning phase (constitution; user constraints).

## Project Structure

### Documentation (this feature)

```text
specs/001-parking-fee-calculator/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── command-line.md
```

### Source Code

```text
src/
└── parking_fee/
    ├── __init__.py
    ├── tariff.py       # Immutable tariff data only
    ├── parsing.py      # File reading, JSON parsing, ticket validation
    ├── calculator.py   # Pure integer-only fee calculation
    ├── cli.py          # argv, error mapping, exact output and exit codes
    └── __main__.py     # python -m parking_fee entry point
```

**Structure Decision**: Use the specified single Python package under `src/parking_fee/`. The package boundaries directly implement Constitution Principles I–II and FR-001–FR-013. The `tests/test_cli.py` entries in the traceability table are planned references for the human engineer; this plan creates or changes no file in `tests/` or `.harness/`.

## Acceptance-Criteria Traceability (reference only)

Each acceptance criterion is exercised end-to-end by the indicated human-owned CLI test file. Modules name the production responsibility satisfying the criterion. This table is traceability only; it does not authorize creating or editing tests.

| Acceptance criterion | Module(s) satisfying it | Test file that will verify it |
|---|---|---|
| AC-001 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-002 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-003 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-004 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-005 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-006 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-007 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-008 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-009 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-010 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-011 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-012 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-013 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-014 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-015 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-016 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-017 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-018 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-019 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-020 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-021 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-022 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-023 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-024 | `cli.py` | `tests/test_cli.py` |
| AC-025 | `parsing.py`, `cli.py` | `tests/test_cli.py` |
| AC-026 | `parsing.py`, `cli.py` | `tests/test_cli.py` |
| AC-027 | `parsing.py`, `cli.py` | `tests/test_cli.py` |
| AC-028 | `parsing.py`, `cli.py` | `tests/test_cli.py` |
| AC-029 | `parsing.py`, `cli.py` | `tests/test_cli.py` |
| AC-030 | `parsing.py`, `cli.py` | `tests/test_cli.py` |
| AC-031 | `parsing.py`, `cli.py` | `tests/test_cli.py` |
| AC-032 | `parsing.py`, `cli.py` | `tests/test_cli.py` |
| AC-033 | `parsing.py`, `cli.py` | `tests/test_cli.py` |
| AC-034 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-035 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-036 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-037 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-038 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-039 | `parsing.py`, `calculator.py`, `cli.py` | `tests/test_cli.py` |
| AC-040 | `parsing.py`, `cli.py` | `tests/test_cli.py` |
| AC-041 | `parsing.py`, `cli.py` | `tests/test_cli.py` |
| AC-042 | `parsing.py`, `cli.py` | `tests/test_cli.py` |
| AC-043 | `parsing.py`, `cli.py` | `tests/test_cli.py` |

## Complexity Tracking

No constitution violations or unjustified complexity.
