<!--
Sync Impact Report
Version change: unratified scaffold → 1.0.0
Modified principles:
- Unfilled scaffold principle 1 → I. Modular Boundaries and Secret Isolation
- Unfilled scaffold principle 2 → II. Untrusted Input and Deterministic Guardrails
- Unfilled scaffold principle 3 → III. Validated Triage Contract and Explicit Failures
- Unfilled scaffold principle 4 → IV. Independent Evaluation and Acceptance
- Unfilled scaffold principle 5 → V. Minimal Dependencies and Maintainability
Added sections: Technical Constraints; Evaluation and Scope Controls
Removed sections: None
Follow-up TODOs: None
-->
# Support Ticket Triage Assistant Constitution

## Core Principles

### I. Modular Boundaries and Secret Isolation
The library MUST separate deterministic input guarding, prompt construction, the model-client
interface, response parsing and validation, and the thin command-line layer. Prompt text MUST
reside in files under `prompts/`, never in source code. All network access and application reading
of the API key MUST be confined to one small OpenAI client module behind the model-client
interface, so tests can inject a fake client. The key MUST come from `OPENAI_API_KEY` and the
model name from `OPENAI_MODEL`. The command-line layer and harness MAY load these values from an
untracked `.env` file. The values MUST NOT appear in source, logs, error messages, or output.

### II. Untrusted Input and Deterministic Guardrails
Ticket text MUST be treated as untrusted data: it MUST never be executed or used as a file path,
command, or tool argument, and MUST NOT change application instructions or the output schema.
The deterministic input guard MUST reject empty, whitespace-only, and oversized input before any
model call; each such refusal MUST make zero model calls.

### III. Validated Triage Contract and Explicit Failures
The output MUST conform to the output schema contract defined in the specification. Responses
MUST be parsed and validated against that contract before they are returned as triage decisions.
Network, timeout, rate-limit, authentication, and other model or service failures MUST raise a
distinct error type and MUST never be represented as a triage result.

### IV. Independent Evaluation and Acceptance
An independent evaluation harness MUST decide acceptance. Acceptance requires 100 percent schema
validity, 100 percent structural-invariant compliance, 100 percent pass on guardrail cases, and
an aggregate score at or above the threshold and scoring formula stated in the specification
before evaluation begins. A language-model judge MAY contribute to aggregate scoring, but MUST
NOT replace schema validation or invariant checks.

### V. Minimal Dependencies and Maintainability
The runtime MUST use Python 3.12 or later and the official `openai` package as its only
third-party runtime dependency. Solutions MUST prefer simple, maintainable implementations over
unnecessary complexity.

## Technical Constraints

Development tools MAY include `pytest`, `pytest-cov`, `ruff`, `bandit`, and `jsonschema`. The
harness MAY populate `OPENAI_API_KEY` and `OPENAI_MODEL` from an untracked `.env` file; `.env`
files MUST NOT be committed. API keys and credentials MUST NOT be committed or written to
evidence or logs.

## Evaluation and Scope Controls

Before any evaluation, the specification MUST define the output schema contract, structural
invariants, behavioral properties, guardrail rules, evaluation threshold, and scoring formula.
Every acceptance criterion and invariant in the specification MUST map to at least one test or
evaluation case.

The independent harness MUST enforce all of the following deterministic-code quality standards:

- `ruff` reports zero errors.
- `bandit` reports zero medium- or high-severity findings.
- All deterministic tests pass.
- Line coverage of `src/` is at least 90 percent, excluding only the thin OpenAI client module,
  which is exercised by the live evaluation.

The `tests/`, `evals/`, and `.harness/` directories are owned by the human engineer and are
outside the scope of Spec Kit implementation tasks. Generated task lists MUST NOT include tasks
to create or modify those directories, though tasks MAY reference them for traceability. During
implementation and repair, the coding agent MAY change only `src/` and `prompts/`. It MUST NOT
modify the specification, `tests/`, `evals/`, or `.harness/`; delete or weaken tests, assertions,
or evaluation cases; change expected results; lower thresholds; disable guardrails, lint, or
security checks; bypass harness gates; or manually edit recorded results. Marking completed tasks 
in `tasks.md` during implementation is permitted.

## Governance

Constitution amendments MUST be made through the Spec Kit constitution workflow, with the
rationale recorded and the version and amendment date updated. Changes to specification
artifacts MUST be made only through the applicable Spec Kit commands (`specify`, `clarify`,
`plan`, or `tasks`), and each legitimate specification change MUST record its reason.

Versioning MUST follow semantic versioning: MAJOR for backward-incompatible governance or
principle removals or redefinitions, MINOR for new principles or sections or materially expanded
guidance, and PATCH for clarifications and non-semantic refinements. Compliance MUST be reviewed
against this constitution and the specification; the independent harness MUST enforce the
specified acceptance and deterministic-code quality gates before acceptance.

**Version**: 1.0.0 | **Ratified**: 2026-11-01 | **Last Amended**: 2026-11-01
