# Research: Support Ticket Triage Assistant

All requirements supplied for this feature are sufficiently specific; there are no unresolved technical-context questions. This research records the fixed decisions and the relevant SDK integration guidance. It does not change the approved specification.

## Python runtime and dependency boundary

**Decision**: Use Python 3.12+ and the official `openai` package as the only third-party runtime dependency. Use the standard library for JSON handling, regular expressions, environment access, file I/O, and CLI serialization.

**Rationale**: The runtime version and dependency boundary are explicit in the feature input and constitution (V). Separating the dependency behind `ModelClient` allows deterministic tests and avoids requiring network access for library tests (NFR-001).

**Alternatives considered**: Third-party schema, CLI, retry, and dotenv libraries were not selected because the contract and behavior are fully defined and the dependency budget excludes them. No package or requirements manifest is in scope.

## OpenAI client integration

**Decision**: Implement `OpenAIClient.complete()` with the official SDK's `OpenAI` client, configured at call time with `api_key`, `timeout=30.0`, and `max_retries=0`. Use Chat Completions with a system message and exact ticket user message, plus `response_format={"type":"json_object"}`. Do not send a temperature parameter and do not request strict structured outputs. Map only `openai.OpenAIError` to `ServiceError` using `raise ... from None`; do not log or expose the original exception. Return an empty string when the response message content is `None`.

**Rationale**: These request parameters and error semantics are fixed by the feature input and implement FR-003, FR-009–FR-010, and AC-019–AC-020/AC-050–AC-051. Official SDK documentation confirms support for a client API key, timeout configuration, disabling automatic retries with `max_retries=0`, Chat Completions, optional `response_format`, and an optional temperature parameter. `json_object` provides JSON mode rather than schema enforcement, which preserves the requirement that the independent validator detect violations (FR-009).

**Alternatives considered**: Responses API and strict structured outputs are not selected because the requested interface explicitly requires Chat Completions and JSON mode without strict outputs. SDK retries are disabled because the evaluator controls its own maximum of three attempts (FR-019). Passing an explicit temperature is unnecessary and forbidden by the feature input.

**Official references**:

- [openai-python README: supported Python and Chat Completions](https://github.com/openai/openai-python/blob/main/README.md)
- [openai-python README: retries and timeouts](https://github.com/openai/openai-python/blob/main/README.md#retries)
- [Chat Completions create parameters](https://github.com/openai/openai-python/blob/main/src/openai/types/chat/completion_create_params.py)
- [JSON response format parameter](https://github.com/openai/openai-python/blob/main/src/openai/types/shared_params/response_format_json_object.py)
- [OpenAI JSON mode and structured outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI Python SDK exception definitions](https://github.com/openai/openai-python/blob/main/src/openai/_exceptions.py)

**Caveat**: Current OpenAI guidance recommends the Responses API for new integrations, while the SDK documents Chat Completions as supported. This design retains Chat Completions because it is an explicit requirement, not an open choice.

## Strict JSON parsing and contract validation

**Decision**: Use standard-library `json.loads` with an `object_pairs_hook` that rejects duplicate keys in every object and a `parse_constant` callback that rejects `NaN` and infinities. Validate the parsed value and every decision invariant without repairs or normalization; on any failure, raise `InvalidModelOutput` containing the exact unmodified reply.

**Rationale**: The specification makes exact structure and raw-reply preservation acceptance requirements (FR-009, INV-001–INV-007, AC-008–AC-018, AC-030–AC-035, AC-046–AC-049, AC-056). This approach uses only the standard library and keeps the parser deterministic and independent of the model.

**Alternatives considered**: JSON Schema or automatic output repair were rejected. A schema dependency violates the runtime dependency constraint, while repair would hide model violations and is explicitly prohibited.

## Input and command-line handling

**Decision**: Count Python string code points with `len`; reject blank text using `strip()` only for the blank check, without changing the original input; read CLI input as bytes, decode strict UTF-8, remove one initial BOM, and write compact sorted UTF-8 JSON bytes plus one LF.

**Rationale**: These choices directly encode the Unicode clarifications, boundary cases, and exact CLI stream requirements (FR-002, FR-012–FR-013, AC-001–AC-004, AC-022–AC-027, AC-044–AC-045, AC-055).

**Alternatives considered**: Text-mode file reading and newline translation were rejected because they could alter CR/LF boundaries. Trimming ticket text was rejected because length must be measured on the original text.

## Evaluation ownership

**Decision**: Document evaluation behavior and AC traceability but leave the dataset, evaluator, tests, and harness to the human engineer.

**Rationale**: The spec requires an independent evaluator (FR-014–FR-019, EV-001–EV-004), while the constitution explicitly reserves `tests/`, `evals/`, and `.harness/` for the human engineer. No such files are created by this plan.

**Alternatives considered**: Generating evaluator/test artifacts as part of this plan was rejected because it violates the stated ownership boundary.
