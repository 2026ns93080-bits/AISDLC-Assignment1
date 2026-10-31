<!--
Sync Impact Report
Version change: unratified -> 1.0.0
Modified principles: template placeholders -> five Parking Fee Calculator principles
Added sections: Runtime and Security Constraints; Quality and Implementation Boundaries
Removed sections: none
Deferred items: none
-->
# Parking Fee Calculator Constitution

## Core Principles

### I. Modular Separation of Concerns
The application MUST separate input parsing and validation, tariff definition, fee
calculation, and command-line handling. The fee calculation MUST be a pure function
with no input/output operations. The command-line layer MUST remain thin.

### II. Data-Driven Tariff
The grace period, hourly rates, daily cap, and any penalties MUST be defined as data
in one tariff module, separate from the fee calculation function. This keeps tariff
policy distinct from calculation logic.

### III. Integer Money and Durations
Money MUST be represented as whole rupees using integers. Durations MUST be
represented as whole seconds or minutes using integers. Floats MUST NOT be used for
money or durations, including during parsing.

### IV. Deterministic Behavior
The same input file MUST produce byte-identical output. The program MUST NOT use
randomness, read the system clock, or make network calls. The feature specification
MUST state every ordering and rounding rule, including output serialization rules;
the implementation MUST follow those rules.

### V. Explicit Input and CLI Contract
The command line MUST accept exactly one input file path argument and emit a JSON
result on stdout on success, with exit code 0. Invalid input MUST produce exit code 2
and a single-line error message on stderr. Expected errors MUST NOT produce stack
traces. Input validation and error handling MUST be explicit, and invalid input MUST
never produce partial results.

## Runtime and Security Constraints

The tool MUST use Python 3.12 or later and only the Python standard library at
runtime. Development tools including pytest, pytest-cov, ruff, and bandit are
permitted. The program MUST read only the input file supplied to it.

Secrets MUST NOT be exposed in source code. Credentials, API keys, and `.env` files
MUST NOT be committed. The program MUST NOT use `eval`, `exec`, `pickle`, or shell
execution.

## Quality and Implementation Boundaries

An independent harness MUST enforce all of these quality gates: ruff reports zero
errors; bandit reports zero medium- or high-severity findings; all tests pass; line
coverage of `src/` is at least 90%; and every acceptance criterion in the
specification maps to at least one automated test.

The human engineer owns `tests/` and `.harness/`. Generated task lists MUST NOT
include tasks to create or modify those directories, though tasks MAY reference
them for traceability. During implementation and repair, application code MUST be
implemented in `src/` only. The coding agent MUST NOT modify the specification,
`tests/`, or `.harness/`; delete or weaken tests or assertions; lower thresholds;
disable lint or security checks; bypass mandatory harness gates; or manually edit
recorded harness results. Specification artifacts MAY be changed only through the
Spec Kit commands `specify`, `clarify`, `plan`, and `tasks`; every legitimate
specification change MUST record its reason. Marking completed tasks in `tasks.md` 
during implementation is permitted.

Solutions MUST prefer simplicity and maintainability over unnecessary complexity.

## Governance

This constitution governs the Parking Fee Calculator and its implementation
workflow. Amendments MUST be made through the Spec Kit constitution workflow, state
their reason, and update the version and last-amended date. Version numbers follow
semantic versioning: MAJOR for backward-incompatible governance changes, MINOR for
new or materially expanded principles or sections, and PATCH for clarifications and
non-semantic refinements.

Implementation and repair work MUST be reviewed against this constitution. The
independent harness MUST verify the stated quality gates; any failure blocks
acceptance until resolved without weakening or bypassing the gates.

**Version**: 1.0.0 | **Ratified**: 2026-10-31 | **Last Amended**: 2026-10-31
