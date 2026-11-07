# Harness feedback for run 01

The independent harness rejected the current implementation.
Fix the root cause of each finding below.

Rules for this repair:
- Change only files under `src/ticket_triage/` and `prompts/`.
- Do not modify `tests/`, `evals/`, `.harness/`, the specification, plan, tasks or constitution.
- Do not weaken, skip or delete any test; do not lower any threshold; do not disable lint or security checks.
- Do not add dependencies, packaging files or configuration files. Do not open, read, print or modify any .env file.
- Preserve behaviour that already passes. Make only the changes the findings require.

Failed gates: lint, security, policy, prompt, tests, coverage, traceability
Findings: 10

## Finding 1: [lint] SRC_MISSING
- Where: `src/ticket_triage`
- Expected: package present
- Observed: missing
- Evidence:

```text
src/ticket_triage does not exist yet.
```

## Finding 2: [security] SRC_MISSING
- Where: `src/ticket_triage`
- Expected: package present
- Observed: missing
- Evidence:

```text
src/ticket_triage does not exist yet.
```

## Finding 3: [policy] SRC_MISSING
- Where: `src/ticket_triage`
- Expected: package present
- Observed: missing
- Evidence:

```text
src/ticket_triage does not exist yet.
```

## Finding 4: [prompt] PROMPT_MISSING
- Where: `prompts/system.md`
- Evidence:

```text
prompts/system.md is missing or empty.
```

## Finding 5: [tests] TEST_ERROR
- Where: `.py::tests.test_contract`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'ticket_triage'
- Evidence:

```text
ModuleNotFoundError: No module named 'ticket_triage'
```

## Finding 6: [tests] TEST_ERROR
- Where: `.py::tests.test_evaluator`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'ticket_triage'
- Evidence:

```text
ModuleNotFoundError: No module named 'ticket_triage'
```

## Finding 7: [tests] TEST_ERROR
- Where: `.py::tests.test_openai_client`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'ticket_triage'
- Evidence:

```text
ModuleNotFoundError: No module named 'ticket_triage'
```

## Finding 8: [tests] TEST_ERROR
- Where: `.py::tests.test_service`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'ticket_triage'
- Evidence:

```text
ModuleNotFoundError: No module named 'ticket_triage'
```

## Finding 9: [coverage] NO_COVERAGE_DATA
- Where: `src/ticket_triage`
- Expected: >= 90.0%
- Observed: no data
- Evidence:

```text
No coverage data was produced (tests may not have run).
```

## Finding 10: [traceability] COLLECTION_FAILED
- Where: `tests`
- Expected: tests collected
- Observed: e.service import triage
E   ModuleNotFoundError: No module named 'ticket_triage'
=========================== short test summary info ===========================
ERROR tests/test_contract.py
ERROR tests/test_evaluator.py
ERROR tests/test_openai_client.py
ERROR tests/test_service.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!
32 tests collected, 4 errors in 0.61s

- Evidence:

```text
pytest could not collect the tests.
```

