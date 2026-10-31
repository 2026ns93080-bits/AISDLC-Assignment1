# Harness feedback for run 01

The independent harness rejected the current implementation in `src/parking_fee/`.
Fix the root cause of each finding below.

Rules for this repair:
- Change files under `src/parking_fee/` only.
- Do not modify `tests/`, `.harness/`, the specification, plan, tasks or constitution.
- Do not weaken, skip or delete any test; do not lower any threshold; do not disable lint or security checks.
- Do not add dependencies, packaging files or configuration files.
- Preserve behaviour that already passes. Make only the changes the findings require.

Failed gates: lint, security, policy, tests, coverage
Findings: 149 (showing the first 25)

## Finding 1: [lint] SRC_MISSING
- Where: `src/parking_fee`
- Expected: package present
- Observed: missing
- Evidence:

```text
src/parking_fee does not exist yet.
```

## Finding 2: [security] SRC_MISSING
- Where: `src/parking_fee`
- Expected: package present
- Observed: missing
- Evidence:

```text
src/parking_fee does not exist yet.
```

## Finding 3: [policy] SRC_MISSING
- Where: `src/parking_fee`
- Expected: package present
- Observed: missing
- Evidence:

```text
src/parking_fee does not exist yet.
```

## Finding 4: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-001]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 5: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-002]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 6: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-003]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 7: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-004]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 8: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-005]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 9: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-006]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 10: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-007]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 11: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-008]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 12: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-009]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 13: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-010]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 14: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-011]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 15: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-012]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 16: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-013]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 17: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-014]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 18: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-015]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 19: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-016]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 20: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-017]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 21: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-018]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 22: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-019]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 23: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-020]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 24: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-021]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

## Finding 25: [tests] TEST_FAILED
- Where: `tests/test_acceptance.py::test_valid_ticket[AC-022]`
- Expected: see message
- Observed: ModuleNotFoundError: No module named 'parking_fee'
- Evidence:

```text
ModuleNotFoundError: No module named 'parking_fee'
```

