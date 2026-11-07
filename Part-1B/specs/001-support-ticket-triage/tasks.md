---
description: "Implementation tasks for the Support Ticket Triage Assistant"
---

# Tasks: Support Ticket Triage Assistant

**Input**: `specs/001-support-ticket-triage/plan.md`, `specs/001-support-ticket-triage/spec.md`, and the feature contracts and data model.

**Scope**: Implementation changes are limited to `src/ticket_triage/` and `prompts/system.md`. `tests/`, `evals/`, and `.harness/` are human-owned. Do not create or modify files there, dependency manifests, CI configuration, or any other files.

**Credential safety**: No task may open, read, print, or modify any `.env` file. Do not invoke application code or a test/evaluation command that would access one; report a blocked validation command instead.

**Tests**: No test-writing tasks are included. Tests and evaluation assets remain human-owned.

## Phase 1: Setup

**Purpose**: No setup tasks are needed; project and dependency manifests are outside this task list's allowed implementation scope.

---

## Phase 2: Foundational contracts and guardrails

**Purpose**: Establish shared errors, deterministic input handling, and response validation before implementing model access or orchestration.

- [X] T001 Define `ServiceError` with the exact message `Model service unavailable.` and `InvalidModelOutput` retaining the exact original `raw_reply` in `src/ticket_triage/errors.py`; do not log or expose underlying service errors. (Trace: FR-009, FR-010, FR-011; NFR: none; INV: none; GR: none; AC: AC-008-AC-020, AC-030-AC-035, AC-046-AC-051, AC-053, AC-056.)
- [X] T002 [P] Implement the pre-model input guard in `src/ticket_triage/guard.py`: reject `text.strip() == ""` or `len(text) > 4000`, count Unicode code points, preserve the original accepted text, return the six-key `invalid_input` refusal, and make no client or environment access. Exactly 4000 code points must pass. (Trace: FR-002, FR-008, FR-010; NFR: none; INV: INV-007; GR: GR-001; AC: AC-001-AC-004, AC-045.)
- [X] T003 [P] Implement strict parsing and validation in `src/ticket_triage/contract.py`: accept exactly `action`, `category`, `priority`, `summary`, `clarification_question`, and `refusal_reason`; enforce action values `triage|clarify|refuse`, category values `billing|technical|account_access|shipping|other`, priority values `low|medium|high|urgent`, refusal reasons `invalid_input|prompt_injection|not_a_support_ticket`, and action-specific nullability. Enforce summary length 1-200 and clarification-question length 5-200 Unicode code points with a final `?`. Reject duplicate keys at any depth, non-standard JSON constants, non-object JSON, any missing/extra key, wrong types/enums, model-originated `invalid_input`, 13-or-more ASCII digit runs after spaces/hyphens are removed, API-key-pattern matches (`sk-` plus at least 20 allowed ASCII characters), and literal `OPENAI_API_KEY`; never repair or normalize a reply, and raise `InvalidModelOutput` with its exact raw text. (Trace: FR-009, FR-011; NFR: none; INV: INV-001-INV-007; GR: GR-005; AC: AC-008-AC-018, AC-030-AC-035, AC-046-AC-049, AC-056.)

**Checkpoint**: Shared input and output contracts are ready; no model, prompt, or CLI code should precede them.

---

## Phase 3: User Story 1 - Triage one support ticket (Priority: P1)

**Goal**: Provide a library flow that validates one ticket, calls an injectable model client when needed, and returns only a valid triage, clarify, or refusal decision.

**Independent Test**: Using a fake `ModelClient`, process valid triage, clarify, and refusal replies; verify exact decision values, unchanged ticket text in the user message, fixed system instructions, call counts, guard behavior, and distinct sanitized errors without network access.

### Implementation

- [X] T004 [US1] Define the injectable `ModelClient` protocol with `complete(system: str, user: str) -> str` in `src/ticket_triage/model_client.py`; keep it dependency-free so callers can supply deterministic fakes. (Trace: FR-001; NFR: NFR-001; INV: none; GR: none; AC: AC-001-AC-007, AC-019-AC-021.)
- [X] T005 [US1] Implement `OpenAIClient.complete()` in `src/ticket_triage/openai_client.py`: read `OPENAI_API_KEY` and `OPENAI_MODEL` at call time, treat stripped-empty values as missing, configure the official SDK with `timeout=30.0` and `max_retries=0`, send one system and one exact user message using Chat Completions JSON-object mode without a temperature override, return `""` for null content, and map only `openai.OpenAIError` to `ServiceError` without exposing or chaining its details. Do not read `.env` files. (Trace: FR-010; NFR: NFR-001; INV: none; GR: none; AC: AC-019-AC-020, AC-050-AC-051.)
- [X] T006 [US1] Write the invariant system instructions in `prompts/system.md` and implement package-relative, unchanged prompt loading in `src/ticket_triage/prompts.py`. Cover the six-field decision contract, categories and priorities, ambiguity, non-ticket and pure-injection refusals, genuine-ticket-plus-injection handling, and prohibited output patterns; ticket text must remain user data and never be interpolated into the system prompt. (Trace: FR-003-FR-007, FR-011; NFR: none; INV: INV-005-INV-006; GR: GR-002-GR-005; AC: AC-021, AC-036-AC-038.)
- [X] T007 [US1] Implement `triage(ticket_text, client=None)` in `src/ticket_triage/service.py`: run the deterministic guard before default-client construction or environment access; otherwise send the exact ticket text with the fixed loaded prompt through the injected/default client, validate the raw reply, return validated values unchanged, and let `InvalidModelOutput` and fixed-message `ServiceError` remain distinct. (Trace: FR-001-FR-011; NFR: NFR-001; INV: INV-001-INV-007; GR: GR-001-GR-005; AC: AC-001-AC-021, AC-030-AC-035, AC-045-AC-051, AC-056.)

**Checkpoint**: The injectable library flow is independently usable without a CLI or live credentials when a fake client is supplied.

---

## Phase 4: User Story 2 - Triage a ticket from a file (Priority: P2)

**Goal**: Provide the specified byte-exact CLI and executable entry point over the same library service.

**Independent Test**: Invoke `cli.main(argv, client=fake)` with controlled files and replies; verify stdout bytes, stderr bytes, exit codes, BOM and UTF-8 handling, zero stdout on failure, and no raw invalid reply output.

### Implementation

- [X] T008 [US2] Implement `main(argv, client=None)` in `src/ticket_triage/cli.py`: require exactly one argument; read ticket bytes, decode strict UTF-8 without newline translation, remove one leading U+FEFF, and call the service. On decisions, write sorted compact JSON with `ensure_ascii=False` as UTF-8 plus exactly one LF. Map argument, file/decode, service, and invalid-model failures to their specified single stderr lines and exit codes, with empty stdout and no raw-reply output on errors. (Trace: FR-001, FR-011-FR-013; NFR: NFR-001; INV: INV-005-INV-006; GR: GR-001, GR-005; AC: AC-022-AC-029, AC-044-AC-045, AC-055.)
- [X] T009 [US2] Implement exactly one public function, `load_env(path: pathlib.Path) -> None`, in `src/ticket_triage/env_loader.py`: read the supplied path as UTF-8; return silently if missing or unreadable; strip each line, skip blank lines, lines starting with `#`, and lines without `=`; split other lines at the first `=`, strip the name/value, and set only a nonempty name absent from `os.environ`. Never print or log and never raise for malformed lines. Do not invoke this loader on, inspect, print, or modify any `.env` file during implementation or verification. (Trace: FR-010; NFR: none; INV: none; GR: none; AC: none.)
- [X] T010 [US2] Implement the minimal executable wiring in `src/ticket_triage/__main__.py`: import `cli.main` and `env_loader.load_env`, pass the resolved Part-1B configuration path (`Path(__file__).resolve().parents[2] / ".env"`) to the loader, then raise `SystemExit(cli.main(sys.argv[1:]))`; add no other logic or exception handling. Do not execute this entry point or access any `.env` file during implementation or verification. (Trace: FR-001, FR-010; NFR: none; INV: none; GR: none; AC: AC-022-AC-029.)

**Checkpoint**: The CLI and module entry point use the same validated service and conform to the specified stream and exit behavior.

---

## Phase 5: User Story 3 - Evaluate behavior against defined cases (Priority: P3)

**Goal**: Use only the human-owned test and evaluation assets to validate the completed implementation and report any acceptance gaps.

**Independent Test**: Run the available human-owned checks without changing their files, and separately trace observed behavior to every AC from AC-001 through AC-056.

### Read-only validation

- [ ] T011 [P] [US3] Run the existing human-owned test suite (`tests/test_service.py`, `tests/test_contract.py`, `tests/test_openai_client.py`, and `tests/test_cli.py`) and evaluation harness (`evals/dataset.json` and the existing `.harness/` assets) using their documented commands; report commands, exit statuses, and concise results without editing any test, harness, dataset, or specification file. Do not access any `.env` file; if a command would do so, stop that command and report the blocked check. (Trace: FR-014-FR-019; NFR: NFR-001; INV: INV-001-INV-007; GR: GR-001-GR-005; AC: AC-039-AC-043, AC-052-AC-054; EV: EV-001-EV-004.)
- [ ] T012 [P] [US3] Compare implemented behavior in `src/ticket_triage/` and `prompts/system.md` against `specs/001-support-ticket-triage/spec.md` and `specs/001-support-ticket-triage/contracts/acceptance-traceability.md` for AC-001 through AC-056; list each unmet or unverifiable criterion with brief evidence and its gap, without changing any file. (Trace: FR-001-FR-019; NFR: NFR-001; INV: INV-001-INV-007; GR: GR-001-GR-005; AC: AC-001-AC-056.)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No tasks; setup and dependency manifests are outside the allowed implementation scope.
- **Foundational (Phase 2)**: T001 precedes T002 and T003; T002 and T003 may run in parallel after T001.
- **User Story 1 (Phase 3)**: Depends on the foundation; execute T004, T005, T006, then T007 in that order.
- **User Story 2 (Phase 4)**: Depends on User Story 1; execute T008, T009, then T010 in that order.
- **User Story 3 (Phase 5)**: T011 and T012 depend on completion of implementation tasks T001-T010 and may run in parallel; both are read-only.

### User Story Dependencies

- **User Story 1 (P1)**: Depends on the foundational error, guard, and contract modules.
- **User Story 2 (P2)**: Depends on User Story 1's service; its entry point also depends on the CLI and environment-loader modules.
- **User Story 3 (P3)**: Depends on the completed implementation; evaluation assets remain human-owned and are not implemented by these tasks.

### Parallel Opportunities

- After T001, T002 (`guard.py`) and T003 (`contract.py`) are independent edits and can proceed in parallel.
- User Story 1 implementation tasks are intentionally ordered by the required dependency sequence; no parallel source edits are proposed.
- User Story 2 implementation tasks are intentionally ordered; no parallel source edits are proposed.
- After implementation, T011 (test/evaluation run) and T012 (acceptance-criteria gap comparison) are independent read-only checks and can run in parallel.

### Parallel Example: Foundation

```text
Complete T001 first.
Then run T002: implement src/ticket_triage/guard.py
in parallel with T003: implement src/ticket_triage/contract.py.
```

### Parallel Example: User Story 3

```text
After T001-T010 are complete, run T011 (human-owned tests/evaluation)
in parallel with T012 (AC-001 through AC-056 gap comparison).
```

## Implementation Strategy

### MVP First (User Story 1)

1. Complete T001-T003 to establish errors, guard, and strict contract validation.
2. Complete T004-T007 in the specified order to deliver the injectable library triage flow.
3. Validate User Story 1 independently with the human-owned checks and a fake client; do not add or edit tests.

### Incremental Delivery

1. Complete the User Story 1 library flow as the MVP.
2. Add User Story 2's CLI, environment loader, and executable entry point in dependency order.
3. After implementation, run the human-owned tests/evaluation and the full AC comparison as read-only tasks.

## Notes

- Every implementation task is unchecked and identifies exact source/prompt paths plus its FR, NFR, INV, GR, and AC traceability.
- No task creates or modifies `tests/`, `evals/`, `.harness/`, specifications, manifests, CI files, or any path outside `src/ticket_triage/` and `prompts/`.
- The final two tasks are validation-only; any unavailable or blocked check must be reported rather than worked around.
