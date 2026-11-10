Evaluation run 1 reported FAIL, though the aggregate was 81/88 and the guardrails were all OK.
The failing case, N05, was a wrong action (a Layer 3 outcome) and not a contract or invariant violation.
FR-018 and AC-043 define PASS in terms of Layer 1 and 2 checks, guardrail cases and the aggregate.
aggregate() had counted Layer 3 findings as contract failures, which was stricter than the specification.
I fixed it with a three-line change, added two pinning tests, and re-locked the hashes.
The recorded eval-01 evidence stays untouched.

Unlike Part 1A, the protected files did change once in Part 1B, and I should say so. This command shows exactly what changed, so quoting its result rather than claiming nothing changed 


(.venv) PS D:\M.Tech\Semesters\Semester 1\AssignmentWorkspace\AISDLC\Assignment-1-SDD-HE\Part-1B> git diff --stat part1b-harness-ready HEAD -- tests evals .harness
 Part-1B/.harness/README.md          |  1 +
 Part-1B/.harness/evaluator.py       |  4 +++-
 Part-1B/.harness/locked-hashes.json |  9 ++++----
 Part-1B/.harness/reaggregate.py     | 42 +++++++++++++++++++++++++++++++++++++
 Part-1B/tests/test_evaluator.py     | 19 +++++++++++++++++
 5 files changed, 70 insertions(+), 5 deletions(-)
 
 
 Run 1 failed on N05 (wrong action), and the run was recorded as FAIL because of the evaluator defect I then fixed.
The repair (e06da4a) fixed N05, but run 2 failed on A02, where the model omitted a key, a Layer 1 violation.
Both the application and the independent Layer 1 check rejected that reply.
The model isn’t deterministic, so a single run can’t prove cause.



Model and configuration: gpt-4o-mini, no temperature set, up to three attempts per case. The first model name (gpt-6.1-luna) returned model_not_found. That was a configuration problem, not a failure of the application.
Threshold and scoring method: the 17/20 threshold and the formula are in the specification, fixed before any evaluation run.
Runs: five deterministic runs (baseline, initial-generation, harness-defect-fix, repair-01, repair-02) and three evaluation runs (initial-generation, repair-01, repair-02). The labels are in the JSON files.
Failures and repairs: N05 (wrong action), the evaluator defect you fixed, A02 (a missing key, found by Layer 1), the evidence given to the agent, what changed, and the results. Mention the variability.
Review: your ACCEPT or REJECT, what you checked, and limitations: the model is non-deterministic, 22 cases is a small sample, the dataset was written by you and one model checked it, a single model was tested, and the contract.py assumption that a reply is a string.

Use part1b-initial-gen, part1b-harness-ready, part1b-harness-fix and part1b-final-gen as your tag names. For the “protected files” claim, run this and quote the actual result, which will show the one evaluator fix:


git diff --stat part1b-harness-ready HEAD -- tests evals .harness specs/001-support-ticket-triage/spec.md .specify/memory/constitution.md

 Part-1B/.harness/README.md          |  1 +
 Part-1B/.harness/evaluator.py       |  4 +++-
 Part-1B/.harness/locked-hashes.json |  9 ++++----
 Part-1B/.harness/reaggregate.py     | 42 +++++++++++++++++++++++++++++++++++++
 Part-1B/tests/test_evaluator.py     | 19 +++++++++++++++++
 5 files changed, 70 insertions(+), 5 deletions(-)
 
 
 