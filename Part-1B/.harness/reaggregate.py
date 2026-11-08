#!/usr/bin/env python3
"""Recompute the run verdict of a recorded evaluation with the current evaluator rules.

Read-only: it prints a result and writes nothing, so recorded evidence is never edited.
Use it after a harness defect fix to see what a recorded run's verdict is under the corrected rule.

    python .harness/reaggregate.py 1            # evidence/eval-results/eval-01.json
"""

import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".harness"))

import evaluator  # noqa: E402


def main():
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("usage: python .harness/reaggregate.py <run number>")
        return 2
    path = ROOT / "evidence" / "eval-results" / f"eval-{int(sys.argv[1]):02d}.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    results = []
    for case in record["cases"]:
        case = dict(case)
        score = case["score"]
        case["score"] = None if score is None else Fraction(score["exact"])
        results.append(case)
    now = evaluator.aggregate(results)
    then = record["summary"]
    print(f"Recorded run {record['run']} ({record['label']}): {then['result']}, aggregate {then['aggregate_exact']}")
    print(f"Same cases under the current rules:  {now['result']}, aggregate {now['aggregate_exact']}")
    print(f"  contract and invariants ok: {now['contract_and_invariants_ok']}; guardrails ok: {now['guardrails_ok']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
