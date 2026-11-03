# Acceptance-Criterion Traceability

This is a mapping only. Test and evaluation components below are owned by the human engineer; this plan does not create or modify anything under `tests/`, `evals/`, or `.harness/`.

| AC | Module(s) satisfying the behavior | Human-owned verification component |
|---|---|---|
| AC-001 | `guard.py`, `service.py` | `tests/test_service.py` |
| AC-002 | `guard.py`, `service.py` | `tests/test_service.py` |
| AC-003 | `guard.py`, `service.py` | `tests/test_service.py` |
| AC-004 | `guard.py`, `service.py` | `tests/test_service.py` |
| AC-005 | `service.py`, `contract.py` | `tests/test_service.py` |
| AC-006 | `service.py`, `contract.py` | `tests/test_service.py` |
| AC-007 | `service.py`, `contract.py` | `tests/test_service.py` |
| AC-008 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-009 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-010 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-011 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-012 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-013 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-014 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-015 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-016 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-017 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-018 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-019 | `openai_client.py`, `errors.py` | `tests/test_openai_client.py` |
| AC-020 | `openai_client.py`, `errors.py` | `tests/test_openai_client.py` |
| AC-021 | `prompts.py`, `service.py` | `tests/test_service.py` |
| AC-022 | `cli.py`, `service.py` | `tests/test_cli.py` |
| AC-023 | `cli.py`, `service.py` | `tests/test_cli.py` |
| AC-024 | `cli.py`, `service.py` | `tests/test_cli.py` |
| AC-025 | `cli.py`, `guard.py` | `tests/test_cli.py` |
| AC-026 | `cli.py` | `tests/test_cli.py` |
| AC-027 | `cli.py` | `tests/test_cli.py` |
| AC-028 | `cli.py`, `service.py`, `errors.py` | `tests/test_cli.py` |
| AC-029 | `cli.py`, `contract.py`, `errors.py` | `tests/test_cli.py` |
| AC-030 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-031 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-032 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-033 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-034 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-035 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-036 | `prompts/system.md`, `service.py`, `contract.py` | `evals/dataset.json` and human-owned evaluation run |
| AC-037 | `prompts/system.md`, `service.py`, `contract.py` | `evals/dataset.json` and human-owned evaluation run |
| AC-038 | `prompts/system.md`, `contract.py`, `service.py` | `evals/dataset.json` and human-owned evaluation run |
| AC-039 | Human-owned `evals/` dataset-schema validator | `evals/dataset.json` validation |
| AC-040 | Human-owned `evals/` Layer 3 scorer | `evals/` scoring component |
| AC-041 | Human-owned `evals/` Layer 1/Layer 2 scorer | `evals/` Layer 1/Layer 2 scoring component |
| AC-042 | Human-owned `evals/` retry and run-status evaluator | `evals/` evaluator component |
| AC-043 | Human-owned `evals/` aggregate/pass evaluator | `evals/` evaluator component |
| AC-044 | `cli.py`, `service.py` | `tests/test_cli.py` |
| AC-045 | `cli.py`, `guard.py`, `service.py` | `tests/test_cli.py` |
| AC-046 | `contract.py`, `service.py` | `tests/test_contract.py` |
| AC-047 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-048 | `contract.py`, `service.py` | `tests/test_contract.py` |
| AC-049 | `contract.py`, `errors.py` | `tests/test_contract.py` |
| AC-050 | `openai_client.py`, `errors.py` | `tests/test_openai_client.py` |
| AC-051 | `openai_client.py`, `errors.py` | `tests/test_openai_client.py` |
| AC-052 | Human-owned `evals/` retry and scoring evaluator | `evals/` evaluator component |
| AC-053 | `contract.py`, `errors.py`, and human-owned `evals/` invalid-reply classifier | `evals/` invalid-reply handling component |
| AC-054 | Human-owned `evals/` Layer 2 and scoring evaluator | `evals/` forbidden-term check |
| AC-055 | `cli.py` | `tests/test_cli.py` |
| AC-056 | `contract.py`, `errors.py` | `tests/test_contract.py` |

The evaluation-related mappings are traceability only and retain the ownership and scope boundary in Constitution IV and FR-014–FR-019.
