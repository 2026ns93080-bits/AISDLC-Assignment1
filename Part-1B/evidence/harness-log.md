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


Run 2 failed
----------------

This failure is genuine, and it also exposed a bug in my evaluator that I need to fix before you repair anything. First the facts, then the fix.

What the feedback shows

The model answered the dark-mode ticket with a valid clarify decision (“Are you submitting this as a feature request…?”). The gold is triage, other, low. The failed check is L3-ACTION-MISMATCH, not X-DISAGREEMENT, so the validator and my independent checks agree and this is ordinary model behaviour. A feature request clearly states what is wanted, so it belongs under other (“any other genuine support request”), and the gold label is right.

My bug: the run should not have failed

My run printed contract and invariants ok: False, but nothing violated a contract or invariant. FR-018 and AC-043 say a run passes when no case is in error, every case is contract-valid and invariant-valid, every guardrail case passes, and the aggregate is at least 0.85. A wrong action on a non-guardrail case sets that case’s score to 0 (FR-017), but it isn’t a contract or invariant failure. My aggregate() counted Layer 3 findings as contract failures, so any single wrong action failed the whole run. That is stricter than my spec. By the spec’s own rule, eval-01 (81/88, about 0.9205, guardrails all OK, no Layer 1 or 2 violations) is a PASS.

The locked harness is human-owned, and fixing it is legitimate when it contradicts the spec. But a fix made after a FAIL could look like loosening a check to get a pass. So I am documenting it fully: what was wrong, the exact spec text that justifies the fix, and how you found it. I am keeping the original eval-01 record untouched.
