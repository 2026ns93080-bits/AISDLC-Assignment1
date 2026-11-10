# Assignment 1: Spec-Driven Development and Harness Engineering (SEZG534)

AI-Augmented Software Development Life Cycle, BITS Pilani WILP. Individual assignment by Abhinav Mukherjee.

Two small applications were built with the GitHub Spec Kit workflow (constitution, specify, clarify,
plan, tasks, analyze, implement) and validated by an independent harness that the coding agent could
not change:

| Part | Application | Behaviour | Harness |
|---|---|---|---|
| `Part-1A/` | Parking Fee Calculator (command line) | Deterministic | Lint, security, policy, tests, coverage, traceability |
| `Part-1B/` | Support Ticket Triage Assistant (library and command line, OpenAI model) | Non-deterministic | The same deterministic gates, plus a three-layer live evaluation with an exact score |

## Repository layout

```text
Assignment-1-SDD-HE/
├── README.md
├── Part-1A/
│   ├── .github/ .specify/           Spec Kit setup and constitution (.specify/memory/constitution.md)
│   ├── specs/001-parking-fee-calculator/   spec, plan, tasks, research, data model, contracts, checklists
│   ├── src/parking_fee/             application (agent-generated)
│   ├── tests/                       acceptance tests (human-owned)
│   ├── .harness/                    gates, runner, configuration, hash lock (human-owned)
│   └── evidence/                    see "Evidence"
└── Part-1B/
    ├── .github/ .specify/ specs/001-support-ticket-triage/
    ├── src/ticket_triage/           application (agent-generated)
    ├── prompts/system.md            system instructions (agent-generated and repaired)
    ├── tests/                       tests (human-owned)
    ├── evals/dataset.json           22 evaluation cases (human-owned)
    ├── .harness/                    gates, evaluator, evaluation runner, hash lock (human-owned)
    └── evidence/
```

## Requirements

Python 3.12 or later (developed on 3.14) and Git. The commands below are for Windows PowerShell; on
macOS or Linux use `source .venv/bin/activate` and `export PYTHONPATH=src`.
Part 1B additionally needs an OpenAI API key for the live evaluation (a few cents per run). The
deterministic gates and all tests need no key and no network.

## Part 1A: run the application and the harness

```powershell
cd Part-1A
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .harness/requirements.txt

python .harness/run_harness.py --label my-run        # all gates; evidence goes to evidence/harness-results/
```

Run the application on a ticket file (one JSON object):

```powershell
Set-Content -Path ticket.json -Value '{"entry":"2026-01-01 10:00","exit":"2026-01-01 13:10","vehicle_type":"car"}' -Encoding Ascii
$env:PYTHONPATH = "src"
python -m parking_fee ticket.json
```

Expected output: `{"duration_minutes":190,"lost_ticket_penalty":0,"parking_fee":160,"total_fee":160,"vehicle_type":"car"}`

## Part 1B: run the application, the harness and the evaluation

```powershell
cd Part-1B
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .harness/requirements.txt

python .harness/run_harness.py --label my-run        # deterministic gates (no key, no network)
```

Live runs need your own key. Copy `.env.example` to `.env` and fill in two lines of the form
`NAME=value` (no quotes): `OPENAI_API_KEY` and `OPENAI_MODEL`. The real `.env` is git-ignored and is never committed.

```powershell
Copy-Item .env.example .env        # then edit .env
python .harness/check_connection.py                  # optional: one request to confirm the key and model work
python .harness/run_eval.py --label my-run           # 22 cases, three layers, exact score vs the 17/20 threshold
```

Run the application on a ticket file (plain UTF-8 text):

```powershell
Set-Content -Path ticket.txt -Value "I was charged twice for my subscription and need a refund." -Encoding Ascii
$env:PYTHONPATH = "src"
python -m ticket_triage ticket.txt
```

The model is not deterministic, so evaluation results can differ between runs; every run is recorded
and none is overwritten. An `INVALID` evaluation result means a case ended in a service error (key,
model name, quota or network) and says nothing about the application; use `check_connection.py` to find out why.

## How the harness stays independent

- `tests/`, `evals/` (Part 1B), `.harness/`, the specification and the constitution are human-owned.
  The constitution forbids the coding agent from changing them, and the `integrity` gate compares them
  with the hashes in `.harness/locked-hashes.json`. After an intentional change, re-lock with
  `python .harness/run_harness.py --lock` and record the reason (see Part 1B's `evidence/harness-change-log.md`).
- The tests and the evaluator were written from the specification's acceptance criteria and were committed
  before any implementation existed (tags `harness-ready` and `part1b-harness-ready`).
- In Part 1B the evaluator re-implements the contract checks and does not import the application, and a
  test requires it to agree with the application's own validator on every scripted reply.

## Evidence

Each part keeps its evidence under `evidence/`:

| Path | Content |
|---|---|
| `agent-sessions/` | Exported Copilot chats for every Spec Kit step, implementation increment and repair |
| `initial-generation/`, `final-generation/` | The first implementation exactly as the agent produced it, and the final one |
| `harness-results/run-NN.json`, `.log`, `-feedback.md` | Every deterministic harness run and the failure evidence given to the agent |
| `eval-results/eval-NN.json`, `-feedback.md`, `eval-results.json` (Part 1B) | Every live evaluation run, and a copy of the latest |
| `spec-change-log.md` | Each change made to a specification and why |
| `harness-change-log.md` (Part 1B) | The one correction made to the human-owned harness and why |
| `harness-log.md` | The narrative of each part: generation, runs, failure and repair, final review and decision |

Git tags mark the milestones: Part 1A `harness-ready`, `initial-gen`, `final-gen`; Part 1B
`part1b-harness-ready`, `part1b-initial-gen`, `part1b-harness-fix`, `part1b-final-gen`.

## Use of AI

- GitHub Copilot (agent mode) with GitHub Spec Kit generated the constitution, specifications, plans, task lists
  and the application code. Its chats are exported in `evidence/agent-sessions/`.
- An AI assistant (Claude) was used to plan the work, review the specifications, and develop the tests, the
  evaluation dataset and the harness (permitted by the assignment's AI policy), and to draft this README.
  The harness design follows Lab Sheet 1 (Spec Kit workflow) and Lab Sheet 2 (feedforward rules, deterministic
  sensors, bounded repair, audit log).
- The prompts given to Copilot at each Spec Kit step were drafted with the assistant's help. I ran them, reviewed every generated
  artifact, answered the clarification questions, decided which analyze findings to act on, and approved or rejected every change.
- The harness logs, the change logs and the reflection report were written by me from my own notes and the recorded evidence.
- Generated code was not treated as correct because it ran: each part has a recorded human review and an ACCEPT decision
  in its `harness-log.md`.

## Deliverables

- Source and evidence: this repository.
- Demonstration video: **<add the link before submitting>**
- Reflection report: uploaded to the LMS together with the links to this repository and the video.
