Evaluation run 1 reported FAIL, though the aggregate was 81/88 and the guardrails were all OK.
The failing case, N05, was a wrong action (a Layer 3 outcome) and not a contract or invariant violation.
FR-018 and AC-043 define PASS in terms of Layer 1 and 2 checks, guardrail cases and the aggregate.
aggregate() had counted Layer 3 findings as contract failures, which was stricter than the specification.
I fixed it with a three-line change, added two pinning tests, and re-locked the hashes.
The recorded eval-01 evidence stays untouched.