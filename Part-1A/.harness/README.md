# Independent harness (Part 1A)

Human-owned. The coding agent must not modify anything under `.harness/` or `tests/`.
Design follows the feedforward / feedback pattern of Lab Sheet 2, with real linters and tests.
Written with AI assistance (permitted for harness development by the assignment's AI policy).

## One-time setup (from the Part-1A folder)

    python -m venv .venv
    .venv\Scripts\Activate.ps1          # Windows PowerShell
    python -m pip install -r .harness/requirements.txt

## Commands

    python .harness/run_harness.py --lock              # record hashes of protected files (human, once)
    python .harness/run_harness.py --label "<note>"    # run all gates and save evidence

## Gates

| Gate | Tool | Passes when |
|---|---|---|
| integrity | sha256 | tests/, .harness/, spec.md and constitution.md match the lock |
| lint | ruff | zero errors in src/ |
| security | bandit | zero medium or high findings in src/ |
| policy | ast | source follows the constitution and plan (no floats, no argparse, ...) |
| tests | pytest | every test passes |
| coverage | pytest-cov | line coverage of src/parking_fee is at least 90 percent |
| traceability | spec + pytest | every AC id in spec.md appears in a test id; SC-003 has a test |

Results are written to `evidence/harness-results/run-NN.json` and `.log`. A failed run also writes
`run-NN-feedback.md`, which is the only text given back to the coding agent.
