# Independent harness (Part 1B)

Human-owned. The coding agent must not modify anything under `.harness/`, `tests/` or `evals/`.
The design follows Lab Sheet 2 (feedforward rules, deterministic sensors, bounded repair, audit
log) and the three-layer pipeline of the assignment (section 4.6). Written with AI assistance,
which the assignment's AI policy permits for harness development.

## One-time setup (from the Part-1B folder)

    python -m venv .venv
    .venv\Scripts\Activate.ps1                       # Windows PowerShell
    python -m pip install -r .harness/requirements.txt

Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY` and `OPENAI_MODEL`. Never commit `.env`.

## Commands

    python .harness/run_harness.py --lock                 # record hashes of protected files (human, once)
    python .harness/run_harness.py --label "<note>"       # deterministic gates (no network, no key)
    python .harness/run_eval.py --label "<note>"          # live evaluation: dataset, model, 3 layers, score
    python .harness/check_connection.py                   # if an evaluation run is INVALID: why did the model call fail?

## Deterministic gates (`run_harness.py`)

| Gate | Passes when |
|---|---|
| integrity | tests/, evals/, .harness/, spec.md and constitution.md match the lock |
| lint | ruff reports zero errors in src/ |
| security | bandit reports zero medium or high findings in src/ |
| policy | source follows the constitution and plan (network and key access only in the adapter, no print, no temperature, max_retries 0, no blanket except, ...) |
| prompt | prompts/system.md defines the contract and contains no evaluation ticket |
| tests | every test passes (no network, no key) |
| coverage | line coverage of src/ticket_triage is at least 90 percent (OpenAI client module excluded) |
| traceability | every AC id in spec.md appears in a test id |

Results: `evidence/harness-results/run-NN.json` and `.log`; a failed run also writes `run-NN-feedback.md`.

## Live evaluation (`run_eval.py`)

Runs every case in `evals/dataset.json` once with the real model (service errors are retried, up to
three attempts in total), checks layer 1 (contract), layer 2 (invariants and guardrails) and layer 3
(score against gold values), and compares the exact aggregate with the threshold 17/20 declared in
the specification. PASS, FAIL, or INVALID (a case ended in a service error, which is never reported
as a failure of the application). Results: `evidence/eval-results/eval-NN.json`; a FAIL also writes
`eval-NN-feedback.md`, the only text given back to the coding agent. `evidence/eval-results.json` is a
copy of the latest run.
