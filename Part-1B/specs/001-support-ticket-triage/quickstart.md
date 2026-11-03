# Quickstart and Validation Guide

This guide describes how the human engineer can validate the implementation after the runtime package and human-owned test/evaluation components exist. It does not create tests, evaluation data, or harness files.

## Prerequisites

- Python 3.12 or later.
- The official `openai` package installed in the active environment for a live model call.
- For live calls only, nonempty `OPENAI_API_KEY` and `OPENAI_MODEL` values. Do not place credentials in source control or evidence.
- The human-owned test and evaluation components required by the approved specification.

The library and CLI support an injected fake `ModelClient`, so deterministic contract and CLI checks do not require credentials or network access.

## Run the CLI

From the Part-1B project root in PowerShell, configure the source package path and model settings, then pass one existing UTF-8 ticket file:

```powershell
$env:PYTHONPATH = "src"
$env:OPENAI_API_KEY = "<configured-key>"
$env:OPENAI_MODEL = "<configured-model>"
python -m ticket_triage .\ticket.txt
```

Expected behavior: one compact JSON object followed by one LF on success. A blank ticket returns the deterministic `invalid_input` refusal without requiring either model variable. CLI errors have empty stdout and the exact stderr line/exit code in [interfaces.md](./contracts/interfaces.md).

## Validate deterministic behavior

Run the human-owned unit tests with the test runner configured by the engineer. They should use an injected fake client to verify the guard boundaries (empty, whitespace-only, 4000, 4001 code points), exact user-message preservation, system-prompt stability, contract rejection, exception data, and CLI bytes/status.

The acceptance-criterion-to-component mapping is in [acceptance-traceability.md](./contracts/acceptance-traceability.md). In particular, verify duplicate-key and non-finite JSON rejection, exact raw-reply preservation, 12/13-digit and API-key-pattern boundaries, BOM removal, CR/LF counting, UTF-8 non-ASCII serialization, and zero output on CLI error.

## Validate the independent evaluation

The human-owned evaluation must validate its dataset and then apply Layers 1–3 as specified in the feature spec (FR-014–FR-019; EV-001–EV-004). Verify independently that Layers 1 and 2 run for returned decisions and exact raw replies in `InvalidModelOutput`, service errors are retried up to three total attempts, and an unresolved service error makes the run `INVALID`. Do not add or modify evaluator components as part of this plan.

## Reference contracts

- Runtime entity shapes and invariants: [data-model.md](./data-model.md)
- Library, model adapter, and CLI behavior: [interfaces.md](./contracts/interfaces.md)
- Every acceptance criterion's implementation and human-owned verification location: [acceptance-traceability.md](./contracts/acceptance-traceability.md)
