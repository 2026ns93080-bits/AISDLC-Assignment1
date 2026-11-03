# Data Model: Support Ticket Triage Assistant

This feature is stateless: one ticket is processed per invocation and no application data is persisted. The shapes below describe runtime values and, where noted, human-owned evaluation data.

## Ticket

| Field | Type | Constraints |
|---|---|---|
| `text` | `str` | Raw plain-text customer message; input is not trimmed. `text.strip() == ""` or `len(text) > 4000` is rejected before model setup. Python `len` counts Unicode code points. |

The CLI starts from file bytes, decodes strict UTF-8 without newline translation, and removes exactly one leading U+FEFF before creating the ticket text. (FR-001–FR-003, FR-012–FR-013, GR-001)

## Triage decision

A JSON object represented by a Python dictionary with exactly these six keys:

| Key | Type / allowed values | Triage | Clarify | Refuse |
|---|---|---|---|---|
| `action` | string: `triage`, `clarify`, `refuse` | `triage` | `clarify` | `refuse` |
| `category` | string: `billing`, `technical`, `account_access`, `shipping`, `other`; otherwise null | required | null | null |
| `priority` | string: `low`, `medium`, `high`, `urgent`; otherwise null | required | null | null |
| `summary` | string of 1–200 code points; otherwise null | required | null | null |
| `clarification_question` | string of 5–200 code points ending in `?`; otherwise null | null | required | null |
| `refusal_reason` | string: `invalid_input`, `prompt_injection`, `not_a_support_ticket`; otherwise null | null | null | required |

Action and field presence/nullability must be consistent. Only the local deterministic guard can produce `invalid_input`; a model reply with that value is invalid. All output strings are checked for a 13-or-more ASCII digit run after spaces and hyphens are removed, an API-key-pattern match (`sk-` plus at least 20 ASCII alphanumeric/underscore/hyphen characters), and literal `OPENAI_API_KEY`. (FR-002, FR-004–FR-011; INV-001–INV-007; GR-002–GR-005)

## Model reply and errors

| Entity | Fields / behavior |
|---|---|
| Model reply | Exact raw string returned by `ModelClient.complete(system, user)`. It must be strict JSON that parses into a valid decision; duplicates, constants such as `NaN`, extra/missing keys, malformed JSON, and any invariant violation invalidate it. |
| `InvalidModelOutput` | Exception for every invalid raw reply. Its `raw_reply` attribute is the exact original string. Do not sanitize or rewrite this diagnostic value; CLI must never print it. |
| `ServiceError` | Exception for service/configuration/network errors. The fixed message is exactly `Model service unavailable.` and it contains no underlying error, API key, or cause. |

(FR-009–FR-011; INV-001–INV-007)

## Evaluation case and evaluation result (human-owned)

These are specification-defined entities for `evals/` only; they do not imply creation or modification of evaluation files in this plan.

| Entity | Required content and validation |
|---|---|
| Evaluation case | Unique id, input text, tags, gold action, and traces of applicable FR/INV/GR ids. Triage cases also include gold category, gold priority, and key terms. Refusal cases include gold refusal reason. `forbidden_terms`, if present, must be checked case-insensitively against every output string field. |
| Per-case result | Case status and score. A contract/invariant/guardrail failure or wrong action yields `FAIL`, score 0. `InvalidModelOutput` is `FAIL`, one attempt, score 0, with independent Layers 1 and 2 run on its exact raw reply. A service failure after up to three attempts is `ERROR`, excluded from the aggregate. |
| Evaluation run | Arithmetic mean of scored cases and final `PASS`, `FAIL`, or `INVALID`. Any `ERROR` makes the run `INVALID`. A `PASS` requires all contract/invariant checks, all guardrail cases passing, and aggregate score at least 0.85. |

(FR-014–FR-019; EV-001–EV-004)

## Relationships and state

`Ticket` → one `ModelClient` request (except deterministic guard refusals) → one raw `Model reply` → either one validated `Triage decision` or one explicit exception. There is no persisted state. The independent evaluator may process a dataset case once per run and may retry service failures up to two times, but retry policy does not belong to the library or OpenAI client.
