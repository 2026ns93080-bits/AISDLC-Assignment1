# Harness log: Part 1B, Support Ticket Triage Assistant

> Skeleton only. Write every section yourself, in your own words, from your worklog and the
> files in `evidence/`. The assignment's AI policy forbids AI-generated log entries.
> Delete these instruction lines when you are done. Do not invent anything that did not happen.

## 1. Model and configuration

_Provider, model name (from `evidence/eval-results/eval-NN.json`), how many attempts per case,
that no temperature was set, and that no key appears in evidence. No secrets._

## 2. Threshold and scoring method (declared before the final evaluation)

_Where the threshold and the formula are defined in the specification, and that they were fixed
before any evaluation run._

## 3. Harness results

_One row per deterministic run and per evaluation run: number, label, outcome, link to the
evidence file. For each evaluation run say what the three layers found._

| Run | Command | Label | Outcome | Evidence |
|---|---|---|---|---|
|  |  |  |  |  |

## 4. Failures and repair (only meaningful failures that really occurred)

_For each repair: the failing case and check, the exact evidence you gave the coding agent (file in
`evidence/agent-sessions/`), what changed in `src/` or `prompts/`, and the re-evaluation result.
Distinguish service errors (INVALID runs) from application failures. If nothing failed, say so._

## 5. Final human review

_ACCEPT or REJECT, what you checked yourself beyond the automated PASS, known limitations and
residual risks (model variability between runs, cases the dataset does not cover, behaviour the
specification leaves open), and your justification._


---------------------------------------------------------
Expect speckit-analyze to notice that the traceability file places the scoring evaluator under evals/. I put it in .harness/, as the assignment’s layout does. Say that once in your harness log.