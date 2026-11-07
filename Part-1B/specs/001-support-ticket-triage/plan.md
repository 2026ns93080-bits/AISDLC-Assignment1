# Implementation Plan: Support Ticket Triage Assistant

**Branch**: `001-support-ticket-triage` | **Date**: 2026-11-03 | **Spec**: [spec.md](./spec.md)

**Input**: Approved feature specification and implementation constraints supplied for this plan.

## Summary

Build a Python 3.12+ library and one-file command-line tool that turn a single customer ticket into a validated six-field triage decision. A deterministic guard handles empty, whitespace-only, and over-limit text before any model configuration or network access. Other tickets are sent unchanged as user data alongside one invariant system prompt to an injectable model client. The raw JSON reply is strictly parsed and validated; invalid output and service failures remain distinct, sanitized errors. The CLI handles strict UTF-8 file input and byte-exact output. The official `openai` package is the sole third-party runtime dependency. See [research.md](./research.md) for decisions and [contracts/interfaces.md](./contracts/interfaces.md) for public interfaces.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: Official `openai` Python package only at runtime; standard library for all other runtime behavior.

**Storage**: None. Input is one file for the CLI; no application persistence.

**Testing**: Human-owned tests and evaluation components specified in the approved spec. `tests/`, `evals/`, and `.harness/` are not generated or modified by this plan.

**Target Platform**: Python 3.12+ environments with access to the configured OpenAI service when model-assisted triage is required.

**Project Type**: Python library plus command-line interface.

**Performance Goals**: No latency or throughput target is specified. The OpenAI client timeout is 30 seconds; deterministic checks are local.

**Constraints**: Exactly one third-party runtime dependency; fixed six-key contract; Unicode code-point length counting; no response repair; sanitized service errors; no output of specified sensitive patterns; the system prompt is identical for each ticket. No project/dependency manifest, tests, evals, or harness files are in scope. `.env` files must not be opened or read during this planning task.

**Scale/Scope**: One ticket per library or CLI invocation; no history, persistence, attachments, UI, or multi-ticket processing.

## Constitution Check

### Pre-design gate

| Principle / constraint | Plan decision | Status |
|---|---|---|
| I. Modular boundaries and secret isolation | Separate guard, prompt loading, model protocol/client, contract parsing, service orchestration, CLI, and optional `__main__` environment loading. Only `openai_client.py` reads model credentials and performs network activity. | PASS |
| II. Untrusted input and deterministic guardrails | Treat the user message strictly as ticket data; reject invalid length/blank input before client creation or environment access. | PASS |
| III. Validated contract and explicit failures | Validate every raw reply without normalization; distinguish `InvalidModelOutput` from fixed-message `ServiceError`. | PASS |
| IV. Independent evaluation and acceptance | Keep the human-owned evaluation harness independent; map every AC in [acceptance-traceability.md](./contracts/acceptance-traceability.md). Do not produce or change evaluation files. | PASS |
| V. Minimal dependencies and maintainability | Python 3.12+, official `openai` package only at runtime, otherwise standard library; use direct, small modules. | PASS |
| Evaluation and scope controls | Do not create or alter `tests/`, `evals/`, or `.harness/`; no change to thresholds or harness behavior. | PASS |

No violations or complexity exceptions are required.

### Post-design gate

The proposed package and prompt tree preserves the boundaries and constraints above. Runtime secrets remain isolated to the OpenAI client; deterministic input refusals need no configuration. Evaluation traces are documentation only and point to human-owned components. The generated plan artifacts stay under `specs/001-support-ticket-triage/`. **Result: PASS; no unresolved clarifications.**

## Architecture and Key Decisions

1. **Small, injectable module boundaries**: `guard.py` performs deterministic input validation; `contract.py` is pure parsing and invariant validation; `model_client.py` defines the replaceable protocol; `openai_client.py` owns environment reads and network access; `service.py` composes them; `cli.py` owns argument, file, and stream behavior. This satisfies Constitution I and V, NFR-001, FR-001–FR-002, FR-009–FR-013, and INV-001–INV-007.
2. **Input gate precedes all external state**: The service checks exactly `text.strip() == ""` or `len(text) > 4000` without trimming the original ticket. It returns the deterministic `invalid_input` decision without creating a default client or reading environment configuration. This implements FR-002, FR-008, GR-001, and AC-001–AC-004/AC-045.
3. **Fixed prompt and untrusted user message**: Load `prompts/system.md` relative to the package location and send it unchanged for each call; pass the exact ticket text only as the user message. The prompt requires the JSON contract and addresses categories, priority, ambiguity, refusals, prompt injection, embedded instructions, and prohibited output. This implements FR-003–FR-007, GR-002–GR-005, and AC-021/AC-036–AC-038.
4. **Strict contract; no repair**: Decode with `json.loads`, reject duplicate keys at every object depth via `object_pairs_hook`, reject non-standard constants via `parse_constant`, and validate exact keys, types, enums, action-field consistency, lengths, refusal provenance, and prohibited patterns. Raise `InvalidModelOutput` with the exact original string on every failure. This implements FR-009, FR-011, INV-001–INV-007, and SC-001/SC-003.
5. **Explicit OpenAI adapter and safe service errors**: Create the client inside `complete()` after verifying stripped, nonempty `OPENAI_API_KEY` and `OPENAI_MODEL`; configure 30-second timeout and no SDK retries; make one Chat Completions JSON-object request without a temperature override. Return `""` for null content. Catch only `openai.OpenAIError` and raise `ServiceError` with no cause or underlying text. This implements FR-010, NFR-001, and AC-019–AC-020/AC-050–AC-051. Evaluation retries, where applicable, belong to the separate human-owned evaluator (FR-019), not the library client.
6. **Byte-defined CLI behavior**: Accept exactly one path, read bytes, strictly decode UTF-8 without newline translation, remove one leading U+FEFF, then call the same library function. Serialize with sorted keys, compact separators, and `ensure_ascii=False`; write UTF-8 plus one LF to the binary stream. Catch only the specified service/contract errors at the CLI boundary and map file/argument failures separately. This implements FR-012–FR-013 and AC-022–AC-029/AC-044–AC-045/AC-055.
7. **Evaluation remains independently owned**: The specification’s dataset, scoring, retries, and run status requirements are traced to the human-owned `evals/` components. This plan neither implements nor creates evaluation or test files, consistent with Constitution IV and its scope controls. FR-014–FR-019, EV-001–EV-004, and AC-039–AC-043/AC-052–AC-054 are verification references only.
8. **Optional `.env` convenience belongs only to the executable entry point**: `env_loader.py` exposes exactly one public function, `load_env(path: pathlib.Path) -> None`. It reads `path` as UTF-8 and returns silently if the file is missing or unreadable. For each line, it strips surrounding whitespace and skips blank lines, lines starting with `#`, and lines without `=`. For other lines it splits at the first `=`, strips whitespace around the name and value, and sets `os.environ[name] = value` only when the name is nonempty and not already in `os.environ`. It never prints or logs and never raises for a malformed line. Library calls do not load `.env`. `__main__.py` imports `cli.main` and `env_loader.load_env`, calls `load_env(Path(__file__).resolve().parents[2] / ".env")` to locate `.env` in the Part-1B project root (the parent of `src`), then raises `SystemExit(cli.main(sys.argv[1:]))`. It contains no other logic and catches no exceptions. No `.env` file is opened, read, printed, or modified during planning. This respects Constitution I and FR-010.

## Project Structure

### Documentation (this feature)

```text
specs/001-support-ticket-triage/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── interfaces.md
    └── acceptance-traceability.md
```

### Runtime source and prompt

```text
src/
└── ticket_triage/
    ├── __init__.py
    ├── __main__.py
    ├── errors.py
    ├── guard.py
    ├── contract.py
    ├── model_client.py
    ├── openai_client.py
    ├── prompts.py
    ├── service.py
    ├── cli.py
    └── env_loader.py
prompts/
└── system.md
```

`tests/`, `evals/`, and `.harness/` are human-owned and deliberately omitted from the generated project tree. No packaging manifest or requirements file is planned.

**Structure Decision**: One importable package under `src/ticket_triage/` with an external prompt file under `prompts/`. This keeps deterministic logic independently testable and confines credentials/network use to one adapter. The CLI is thin and calls the same service as the library.

## Requirement Coverage

- **Library and CLI**: FR-001, FR-012–FR-013; NFR-001.
- **Deterministic guard and untrusted prompt**: FR-002–FR-008; GR-001–GR-004.
- **Response validation and privacy**: FR-009, FR-011; INV-001–INV-007; GR-005.
- **OpenAI integration and failure mapping**: FR-010; AC-019–AC-020, AC-050–AC-051.
- **Independent dataset/evaluation policy**: FR-014–FR-019; EV-001–EV-004; verification mapping only, not generated evaluator code.
- **Acceptance traceability**: Every criterion AC-001 through AC-056 has a module mapping and a human-owned test/evaluation verification component in [acceptance-traceability.md](./contracts/acceptance-traceability.md).

## Complexity Tracking

No constitution violations; no additional architectural complexity is proposed.
