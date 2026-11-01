# Harness log: Part 1A, Parking Fee Calculator


## 1. Initial generation and context


The agent received the constitution, spec, plan and tasks, plus the data model, research and contract files. The tests and harness files were not provided to the agent. The agent was told not to modify those files.

Project Constitution (constitution.md): Located under ".specify/memory/constitution.md", outlining engineering rules, guardrails, and coding standards.

Specification (spec.md) : It is located - "specs/001-parking-fee-calculator/spec.md". It defines exact functional requirements, data keys, integer types (e.g., FR-012), and acceptance criteria (e.g., AC-043 regarding duplicate key rejection).

Implementation Plan (plan.md): The implementation plan directly aligned with the specification and acceptance criteria.

Task Breakdown (tasks.md): The granular, sequenced task list (ranging from T001 to T010) that guided the agentic implementation steps. The agent did T001 to T008.


Then the implementation was executed across 3 distinct code-generation increments (commits), followed by harness evaluations and a repair iteration.
- Implementation Increments
- Increment 1 : Commit Message: Part-1A: implement T001-T005 (agent-generated)
- Tasks Covered: T001 through T005 (Package initializer, frozen tariff rules, pure integer-only fee calculation, valid ticket parsing and handling the main entry point).

- Increment 2 : Commit Message: Part-1A: implement T006 (agent-generated)
- Tasks Covered: T006 (capped fee calculation).

- Increment 3 : Commit Message: Part-1A: implement T007-T008 (agent-generated)
- Tasks Covered: T007 and T008 (strict failure handling in parsing.py, error contract in cli.py).

I ran the harness myself. This was not given to the agent.

During the initial generation, the agent could change src/parking_fee/ only, run no commands, and tick tasks.

The untouched first version is in evidence/initial-generation/ and tag "initial-gen".




## 2. Harness executions

Run 01 was a baseline before any code existed, not a repair cycle.

| Run | Label | Outcome | Evidence |
|---|---|---|---|
| Run 01 | baseline-no-implementation | Failed (lint, security, policy, tests, coverage), Integrity and traceability passed | evidence/harness-results/run-01.json |
| Run 02 | initial-generation |Failed (Lint gate failed: RUFF_UP042, RUFF_UP035), all other gates passed |evidence/harness-results/run-02.json |
| Run 03 | repair-01 | Passed | evidence/harness-results/run-03.json |
| Run 04 | verify-committed-final | Passed | evidence/harness-results/run-04.json |

## 3. Failure and repair


Failed Gate: lint
- Failures / Findings:
- Finding 1:
- Rule: RUFF_UP042, File: src/parking_fee/parsing.py, Line: 15
- Description: Class ErrorCode inherits from both str and enum.Enum.

- Finding 2:
- Rule: RUFF_UP035, File: src/parking_fee/tariff.py, Line: 3
- Description: Import Mapping from collections.abc instead of typing.

The exact text given to the agent for the repair iteration was provided via file:
File Name: evidence/agent-sessions/13-repair-01.json (I pasted the contents of run-02-feedback.md into a new chat and saved as 13-repair-01.json)

The agent made two adjustments under src/parking_fee/ to resolve the Ruff linter violations:

- In parsing.py:
- Change: Switched the inheritance of the ErrorCode class from (str, Enum) to StrEnum.
Instead of inheriting from both str and enum.Enum separately (which triggers Ruff rule RUFF_UP042), the agent modified it to use Python's built-in StrEnum imported from the 
enum module. The class now uses StrEnum as the lint rule asks.

- In tariff.py:
- Change: Moved the import of Mapping from typing to collections.abc.
To comply with Ruff rule RUFF_UP035 (which discourages importing collection types from typing in favor of standard collections), the agent removed Mapping from the typing import 
statement and added a dedicated import from collections.abc import Mapping.


In Run-03, same gates passed on the re-run, and all tests, harness files, specifications, and threshold configurations were left completely untouched.

- Run-03 passed on local folder
- The harness results were committed
- However, I noticed the src changes were still uncommitted
- The src was later committed (b76bb58) - final-gen tag
- Run-04 on the committed code gave the same source hash and a pass

Running "git diff --stat harness-ready HEAD -- tests .harness specs/001-parking-fee-calculator/spec.md .specify/memory/constitution.md" produces empty output (0 files changed).
This explicitly proves none of these files (tests,harness,spec.md & constitution.md) differ from the harness-ready commit.


## 4. Final human review


Beyond relying on the automated PASS from the harness, I conducted a manual inspection of the final source code in src/parking_fee/.

I went over the codebase manually and verified the following:

Arithmetic & Policy Compliance: I audited calculator.py to ensure zero use of float types or standard division (/). All monetary and time calculations strictly use integer arithmetic (// and integer multiplication). I also confirmed that argparse is not imported, keeping command-line handling aligned with the required policy gate.

Input Robustness (BOM, Duplicates, Recursion): I verified that a custom object_pairs_hook is implemented to detect and reject duplicate keys at any nesting depth (satisfying AC-043 / FR-003 and FR-013), and that the code catches RecursionError at parsing.py:112.
The code requires a regular file, reads it in binary mode and rejects empty bytes, leading UTF-8 BOM, invalid UTF-8/JSON, non-finite JSON constants, parser recursion errors, and non-object top-level values.

Centralized Error Handling: I verified that the codebase contains no blanket except: or generic except Exception: clauses. All operational failures catch specific exception types and map cleanly through a single error-handling function. Errors are raised as ParkingFeeError with an ErrorCode, and error_message() in cli.py is the one place that turns a code into the text 
from FR-013.
The exception list includes - 

ParkingFeeError (cli.py:34) - Catches ParkingFeeError, which every expected failure raises
ValueError (parsing.py:79) -  Impossible-calendar-date check
OSError, ValueError (parsing.py:88 and 96) - Handles error when file cannot be read
UnicodeDecodeError (parsing.py:103) -  Handles invalid UTF-8 bytes
ValueError, RecursionError (parsing.py:112) - Handles error while decoding invalid json, duplicate keys and non-finite constants

Plan Alignment & Scope Control: I confirmed that there are exactly six .py files in src/parking_fee. No packaging files were added. The policy gate in .harness/run_harness.py enforces standard-library-only imports.

Known Limitations

- Code catches RecursionError and no test covers it.
- Handling of Year 0000 and years above 9999 are unspecified.
- One ticket per file, and no time zones or daylight saving adjustment.
- The tests and spec were written by the same person, so a misreading of the spec would pass the harness.
- NFR-003 ("no stack trace") holds only for expected failures as main only catches ParkingFeeError. If the code ever hit an unexpected bug, we would get a Python traceback.

My decision to ACCEPT this build rests on the following justification - 

An automated harness PASS is necessary but insufficient on its own. The manual code review confirms that the codebase respects all architectural constraints:
- It maintains integer-only financial math.
- Robust Error Handling covering scenarios - ticket parsing, file read error, invalid bytes or json.
- No argparse import, and no float or / in the code.
- Run-04 passed every gate, there are six source files, no packaging files, and no blanket except.

My decision to ACCEPT the current implementation is justified.