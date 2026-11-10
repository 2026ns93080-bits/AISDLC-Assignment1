# Harness log: Part 1B, Support Ticket Triage Assistant

This is the harness log for the Part 1B of the assignment.

## 1. Model and configuration
Initially, OpenAI gpt-6.1-luna model was chosen, but I received model_not_found  error.
That was a configuration problem, not a failure of the application.
Then I used the popular and cheap OpenAI model - gpt-4o-mini.
No temperature set, up to three attempts per case.
Model is recorded in configuration.model in each eval-NN.json.

Actual API key does not appear in the evidence. A fake sample key is visible in the dataset and test.

git grep -nE "sk-[A-Za-z0-9_-]{40,}" returns nothing. So, actual API key is not exposed.


## 2. Threshold and scoring method (declared before the final evaluation)
Threshold is defined as 0.85 (FR-018, EV-003) and the formula in FR-017.
Threshold is fixed before any evaluation.

The command - git log --oneline -- specs/001-support-ticket-triage/spec.md shows the commits as per sequence. See below.

9448667 Part-1B: spec - coverage for key handling, retries, invalid output evaluation, forbidden terms, UTF-8 output
18c34f3 Part-1B: clarified spec - boundary criteria and testability
0942992 Part-1B: clarified spec - evaluation of invalid output, key handling, file reading
4451efd Part-1B: specification (draft before clarification)

## 3. Harness results

5 Deterministic runs followed by 3 Evaluation (Non-deterministic) runs as provided in below table - 

Deterministic Runs

| Run | Command | Label | Outcome | Evidence |
|---|---|---|---|---|
| 1 | run_harness.py | baseline-no-implementation | FAIL (lint, security, policy, prompt, tests, coverage, traceability) | evidence/harness-results/run-01.json |
| 2 | run_harness.py | initial-generation | PASS | evidence/harness-results/run-02.json |
| 3 | run_harness.py | harness-defect-fix | PASS | evidence/harness-results/run-03.json |
| 4 | run_harness.py | repair-01 | PASS | evidence/harness-results/run-04.json |
| 5 | run_harness.py | repair-02 | PASS | evidence/harness-results/run-05.json |

Evaluation (Non-deterministic) Runs 

| 1 | run_eval.py | initial-generation | FAIL, aggregate 81/88 | evidence/eval-results/eval-01.json |
| 2 | run_eval.py | repair-01 | FAIL, aggregate 81/88 | evidence/eval-results/eval-02.json |
| 3 | run_eval.py | repair-02 | PASS, aggregate 427/440 | evidence/eval-results/eval-03.json |

eval 1 (initial-generation) - failed (N05) due to action mismatch
eval 2 (repair-01) - failed (A02) due to missing key
eval 3 (repair-0) - passed

Note - The generated plan placed the scoring evaluator under evals/, but the assignment’s layout puts the evaluators in .harness/ and only dataset.json in evals/.


## 4. Failures and repair (only meaningful failures that really occurred)
Evaluation Run 1: failed (N05). 
Reason for failure - the model asked a clarifying question about a request that states what the customer wants
Evidence given to the agent - 
Change - 

The case failure (N05) was real. The run verdict (FAIL) was affected by the evaluator defect.

repair-01 - The agent was given the file - eval-01-feedback.md and the chat export - 14-repair-1.json

Evaluation Run 2 : A02 failed because the model omitted refusal_reason (a Layer 1 violation; the application and the independent check agreed). This happened after repair-01.

repair-02: The failing case was A02.  Check - L1-MISSING-KEY, refusal_reason. The agent was given the evidence - eval-02-feedback.md, saved in 15-repair-2.json.
Change - One sentence change in prompts/system.md
Result - run 3, all 22 passing, 427/440, with deterministic run 5 passing

No run was INVALID. So there were no service errors during evaluation. The model_not_found was found earlier, by the connection check.

It cannot be concluded if repair-01 caused A02 to fail - because each run was one sample.
M01 changed from 0.9 to 1.0 between runs 2 and 3.

## 5. Final human review

After repair-02, I ACCEPT this build as successful. Both automated tests and manual reviews were performed. Files checked - TBD
src and prompts were unchanged between repair-02 and the final freeze. This is evidenced from the command - git diff --stat ea26b8c HEAD -- src prompts, that returned nothing.

Known Limitations

- Don't put quotes around values in your .env file. For example, OPENAI_API_KEY="sk-..." will store the literal quotation marks in the key, causing authentication to fail. 
(Leaving the quotes off works fine.)
- We need better error handling for unexpected API responses. If OpenAI returns an empty choices list, the code throws an IndexError traceback instead of a clean error message, because we're currently only catching OpenAIError.
- The model tends to be slightly over-eager with priorities. It frequently scored around 0.90, ranking items one priority level higher than our human-annotated gold standard.
The data shows 6 of 13 scored triage cases one level off.
- The evaluation was conducted on a single 22-case synthetic sample created in-house, running each test case only once through a single model. Because model outputs are non-deterministic, these single-run results may vary across executions.
Residual Risks : In real-world deployment, unpredictable edge cases, prompt variations, and live API responses could still trigger unexpected behavior or unhandled exceptions that were not captured in this small offline test set.


