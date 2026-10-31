---

description: "Implementation tasks for the Parking Fee Calculator"
---

# Tasks: Parking Fee Calculator

**Input**: Design documents from `specs/001-parking-fee-calculator/`

**Scope**: Implement and validate application behavior using files under `src/parking_fee/` only. The test suite and `.harness/` are human-owned; do not create or modify them. Do not modify project manifests, CI configuration, or specification files.

**Prerequisites**: `plan.md`, `spec.md`, `data-model.md`, `research.md`, `contracts/command-line.md`, and `.specify/memory/constitution.md`.

**Tests**: No test-writing tasks are included. Run the human-owned tests and harness only in the final verification phase.

**Organization**: Tasks follow the required module dependency order. User-story phases distinguish the valid-ticket MVP, tariff boundaries, and invalid-input behavior; the stories depend on the shared package and on earlier application layers.

## Phase 1: Setup

**Purpose**: Create the application package and its shared tariff source.

- [X] T001 Create the package initializer in `src/parking_fee/__init__.py` and define the frozen tariff record plus one immutable vehicle-keyed tariff mapping in `src/parking_fee/tariff.py`, using a 15-minute grace period and 200-rupee lost-ticket penalty for both vehicles, 20 rupees/hour and a 150-rupee cap for `two_wheeler`, and 40 rupees/hour and a 300-rupee cap for `car`; satisfy FR-007, NFR-002, AC-005–AC-022, and AC-034–AC-039.

---

## Phase 2: Foundational

**Purpose**: No additional infrastructure is required beyond T001; implementation proceeds through the ordered story phases below.

---

## Phase 3: User Story 1 - Calculate a parking fee (Priority: P1) - MVP

**Goal**: Accept a valid ticket and produce its whole-minute duration and predictable fee result.

**Independent Test**: After T005, invoke `python -m parking_fee <path>` with the valid AC-015 car ticket and AC-016 two-wheeler ticket; compare exit status and exact stdout bytes, including the final LF, and confirm stderr is empty.

### Implementation

- [X] T002 [US1] Implement the pure integer-only calculation in `src/parking_fee/calculator.py`: accept the normalized ticket fields `entry_minute`, `exit_minute`, `vehicle_type`, and `lost_ticket`; calculate whole-minute duration, zero parking fee through 15 minutes, started-hour billing after grace without subtracting grace, and the independent lost-ticket penalty; return exactly `duration_minutes`, `lost_ticket_penalty`, `parking_fee`, `total_fee`, and `vehicle_type`; satisfy FR-008–FR-009 and FR-011, NFR-002, AC-001–AC-010, AC-015–AC-016, and AC-020–AC-022.
- [X] T003 [US1] Implement the valid-ticket path in `src/parking_fee/parsing.py`: read a valid supplied file as bytes, decode strict UTF-8 JSON, require an object with string `entry`, `exit`, and `vehicle_type`, default an omitted `lost_ticket` to `false`, validate timestamp shape/calendar/time and supported vehicle values, reject exit-before-entry, and return integer ordinal-minute indices plus normalized fields for T002; satisfy FR-004–FR-006, NFR-002, AC-001–AC-023, and AC-034–AC-039.
- [X] T004 [US1] Implement the success path and reusable interfaces in `src/parking_fee/cli.py`: provide `main(argv)` that passes one input path through parsing and calculation, serializes the five result fields with sorted keys and compact separators, and writes UTF-8 result bytes followed by exactly one LF to `sys.stdout.buffer` with no success output on stderr; satisfy FR-012, NFR-001, AC-001–AC-023, and AC-034–AC-039.
- [X] T005 [US1] Implement the module entry point in `src/parking_fee/__main__.py` by passing `sys.argv[1:]` to `cli.main` and returning its exit status through `SystemExit`, so `python -m parking_fee <path>` invokes the application; satisfy FR-012, NFR-001, AC-015–AC-016.

**Checkpoint**: The valid AC-015 and AC-016 tickets run end to end with exact successful output.

---

## Phase 4: User Story 2 - Apply grace, tariff, caps, and penalties (Priority: P1)

**Goal**: Complete billing for full 1440-minute blocks, residual started hours, caps, and penalty combinations.

**Dependency**: T001–T005 establish the ticket-to-result path; this story completes the daily-cap formula in its calculation layer.

**Independent Test**: Run the valid boundary and multi-day ticket cases through the CLI; compare all result fields and exact output bytes for AC-001–AC-023 and AC-034–AC-039.

### Implementation

- [X] T006 [US2] Complete the capped tariff calculation in `src/parking_fee/calculator.py`: for `D > 15`, use `q = D // 1440`, `r = D % 1440`, `remaining_hours = (r + 59) // 60`, and `q * cap + min(cap, remaining_hours * rate)`; keep all amounts and durations integer-only, the calculator pure, and the lost-ticket penalty independent of parking fee; satisfy FR-007–FR-011, NFR-002, AC-001–AC-023, and AC-034–AC-039.

**Checkpoint**: Grace, hourly rounding, full-day blocks, caps, and lost-ticket combinations match the specified end-to-end results.

---

## Phase 5: User Story 3 - Receive a precise error for invalid input (Priority: P1)

**Goal**: Reject malformed arguments, files, JSON, and ticket fields in the specified order without partial output or traceback.

**Dependency**: Requires the parser and CLI interfaces from User Story 1; the completed fee calculation from User Story 2 remains unchanged.

**Independent Test**: Run each invalid-input and precedence vector in AC-024–AC-033 and AC-040–AC-042; verify exit status 2, empty stdout, and exactly the specified UTF-8 error line plus one LF on stderr.

### Implementation

- [ ] T007 [US3] Complete strict failure handling in `src/parking_fee/parsing.py`: require a regular file and fully read it in binary mode; reject empty bytes, a leading UTF-8 BOM, invalid UTF-8/JSON, duplicate object keys, non-finite JSON constants, parser recursion errors, and non-object top-level values; validate `entry`, `exit`, `vehicle_type`, `lost_ticket`, then chronological order in the specified precedence; expose explicit expected error codes and handle only expected boundary exceptions; satisfy FR-002–FR-006 and FR-013, NFR-003, AC-025–AC-033, AC-041–AC-043.
- [ ] T008 [US3] Complete the failure contract in `src/parking_fee/cli.py`: check only `len(argv)` for exactly one argument, treat option-looking arguments as paths, map parser/file/argument error codes to the exact FR-013 messages, return 2, write no stdout bytes on failure, and write exactly one UTF-8 message line plus LF to `sys.stderr.buffer`; do not use an option parser or blanket exception handler; satisfy FR-001, FR-012–FR-013, NFR-001 and NFR-003, AC-024–AC-033, and AC-040–AC-043.

**Checkpoint**: All invalid-input cases preserve first-failure precedence and emit only the contracted error output.

---

## Phase 6: Polish & Cross-Cutting Verification

**Purpose**: Run the human-owned quality gates and report any remaining acceptance gaps without changing protected files.

- [ ] T009 Run the human-owned test suite with `python -m pytest` and run the existing `.harness/` gates using their prescribed invocation against `src/parking_fee/__init__.py`, `src/parking_fee/tariff.py`, `src/parking_fee/calculator.py`, `src/parking_fee/parsing.py`, `src/parking_fee/cli.py`, and `src/parking_fee/__main__.py`; report commands, pass/fail results, coverage and lint/security outcomes, and failures without editing any test, harness, or specification file; for SC-003, confirm that human-owned tests invoke each acceptance case at least twice with identical arguments, file bytes, and file availability and compare stdout bytes, stderr bytes, and exit status; if no such test exists, report SC-003 as unverifiable and recommend blocking acceptance pending a human-owned test update; verify FR-001–FR-013, NFR-001–NFR-003, and AC-001–AC-043.
- [ ] T010 Compare implemented behavior in `src/parking_fee/__init__.py`, `src/parking_fee/tariff.py`, `src/parking_fee/calculator.py`, `src/parking_fee/parsing.py`, `src/parking_fee/cli.py`, and `src/parking_fee/__main__.py` against AC-001 through AC-043, then list each unmet or unverifiable criterion and its evidence without changing any file; list SC-003 evidence alongside the AC-001 through AC-043 comparison; verify FR-001–FR-013, NFR-001–NFR-003, and AC-001–AC-043.

---

## Dependencies & Execution Order

### Required module order

1. T001 creates the package skeleton and immutable tariff data.
2. T002 implements the calculator.
3. T003 implements ticket parsing and normalization.
4. T004 implements CLI behavior; T005 adds the `python -m parking_fee` entry point.
5. T006 completes tariff-cap behavior; T007 and T008 add strict validation and failure output without changing the module dependency order.
6. T009 runs the human-owned gates; T010 performs the final AC-001–AC-043 gap comparison.

### User-story dependencies

- **US1 (P1)**: Starts after T001; completes at T005. It is the MVP and provides the valid-ticket pipeline.
- **US2 (P1)**: Depends on the US1 pipeline and completes at T006.
- **US3 (P1)**: Depends on the US1 parser/CLI interfaces and follows US2 in this execution plan; it completes at T008.
- **Final verification**: T009 follows implementation; T010 follows T009 and makes no changes.

### Parallel opportunities

No implementation task is marked `[P]`: each module depends on the preceding interface in the user-required order. The two final checks also remain ordered so the harness report precedes the final acceptance-gap report.

## Implementation Strategy

Deliver the valid-ticket MVP first (T001–T005), then complete daily caps and multi-day billing (T006), then strict error precedence and byte-exact failures (T007–T008). Finish by running, not modifying, the human-owned checks and listing any remaining acceptance gaps (T009–T010).
