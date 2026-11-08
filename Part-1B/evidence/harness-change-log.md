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