# Interface Contracts

The public library and CLI are separate entry points over one service. The model protocol is injectable so callers and human-owned tests can control model replies without network access (NFR-001).

## Library

```text
triage(ticket_text: str, client: ModelClient | None = None) -> dict
ModelClient.complete(system: str, user: str) -> str
```

- Check the deterministic guard first. Empty/whitespace-only or over-4000-code-point input returns the six-key `invalid_input` refusal with zero client creation, environment lookup, or model calls.
- For other input, use the injected client or create `OpenAIClient`; send the fixed loaded system prompt and the exact ticket text as the user message.
- Parse and validate the raw reply with the complete decision contract. Return validated values unchanged, or raise `InvalidModelOutput` with exact `raw_reply`.
- Raise `ServiceError` for model configuration/service errors. Its message is exactly `Model service unavailable.`.

## Decision JSON object

Every successful library result has exactly these keys: `action`, `category`, `priority`, `summary`, `clarification_question`, and `refusal_reason`. Types, enums, action-dependent nullability, code-point length rules, refusal provenance, and sensitive-pattern exclusions are defined in [data-model.md](../data-model.md) and the approved [specification](../spec.md) (FR-004–FR-011; INV-001–INV-007).

The reply parser does not accept duplicate object keys (at any depth), non-standard JSON constants, non-object JSON, missing or extra keys, wrong types/enums, or any invariant violation. It performs no repair, inference, or normalization.

## OpenAI adapter

`OpenAIClient.complete(system, user)`:

1. Read `OPENAI_API_KEY` and `OPENAI_MODEL` at call time; strip only to determine whether each is missing/empty. If either is empty, raise `ServiceError` before network activity.
2. Construct the official client with `api_key=...`, `timeout=30.0`, and `max_retries=0`.
3. Call Chat Completions with one system message, one user message, and `response_format={"type":"json_object"}`. Do not set temperature or strict structured outputs.
4. Return the response content string, or `""` if content is `None`.
5. Catch only `openai.OpenAIError` and raise the fixed `ServiceError` with no chained underlying cause. Do not log, print, or expose credentials or SDK error text.

The model itself must produce the JSON-object response specified in `prompts/system.md`; independent contract parsing remains mandatory.

## CLI

```text
main(argv: list[str], client: ModelClient | None = None) -> int
```

- Exactly one argument is required. Do not interpret options.
- Read the named file as bytes; strict UTF-8 decode with no newline translation; remove one leading U+FEFF if present; then invoke `triage`.
- Successful decisions, including refusals, are serialized as `json.dumps(decision, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` encoded UTF-8, followed by exactly `b"\n"` on `sys.stdout.buffer`. Exit 0.
- Failures write no stdout bytes and exactly one LF-terminated message to `sys.stderr.buffer`:

| Condition | Exit | Stderr line |
|---|---:|---|
| Argument count is not one | 2 | `error: expected exactly one input file path` |
| Missing, directory, unreadable file, or invalid UTF-8 | 2 | `error: cannot read input file` |
| `ServiceError` | 3 | `error: model service unavailable` |
| `InvalidModelOutput` | 4 | `error: model returned an invalid response` |

The CLI must not print raw invalid replies or any partial/success-shaped JSON on error (FR-012–FR-013).

## Executable entry point and configuration

`python -m ticket_triage` may load key/value entries from an untracked `.env` file in the Part-1B root via `env_loader.py`, setting only environment names not already set, then call `cli.main`. The library modules never read `.env`. The plan has not opened or read any `.env` file. Only `OPENAI_API_KEY` and `OPENAI_MODEL` are consumed by the OpenAI adapter.
