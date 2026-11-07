#!/usr/bin/env python3
"""Single evaluation harness for the Support Ticket Triage Assistant (Part 1B).

Owned by the human engineer. The coding agent must not modify anything in .harness/.
Design follows the bounded feedback loop of Lab Sheet 2, Part C (dataset -> model call ->
checks -> score -> structured failure evidence), but the checks are independent of the
application (see evaluator.py) and the score is exact.

Usage (from the Part-1B folder, virtual environment active, OPENAI_API_KEY and OPENAI_MODEL
set in the environment or in the untracked .env file):

    python .harness/run_eval.py --label "initial-generation"

Pipeline (assignment section 4.6):
    evals/dataset.json -> triage() with the real OpenAI client -> schema validation (layer 1)
    -> invariant and property checks (layer 2) -> semantic/quality score (layer 3)
    -> aggregate score against the threshold declared in the specification.

Evidence written (never overwritten):
    evidence/eval-results/eval-NN.json         full structured result for run NN
    evidence/eval-results/eval-NN-feedback.md  failure evidence for the coding agent (FAIL runs)
    evidence/eval-results.json                 copy of the latest run (assignment layout)

Run result: PASS (exit 0), FAIL (exit 1), INVALID because a case ended in a service error
(exit 3). Service errors are never reported as evaluation failures. The key is never printed
or written anywhere.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".harness"))
sys.path.insert(0, str(ROOT / "src"))

import evaluator  # noqa: E402

DATASET = ROOT / "evals" / "dataset.json"
RESULTS_DIR = ROOT / "evidence" / "eval-results"
LATEST = ROOT / "evidence" / "eval-results.json"
MAX_FEEDBACK_CASES = 12
MAX_TEXT = 700


# --------------------------------------------------------------------------------------
# Environment (the key is read, never shown)
# --------------------------------------------------------------------------------------


def load_env_file(path):
    """Set variables from KEY=VALUE lines for names that are not already set."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name, value = name.strip(), value.strip()
        if name and value and name not in os.environ:
            os.environ[name] = value


# --------------------------------------------------------------------------------------
# Running the application once per attempt
# --------------------------------------------------------------------------------------


class CountingClient:
    """Wraps a model client and counts calls, so guard-refused input can be proven call-free."""

    def __init__(self, inner):
        self.inner = inner
        self.calls = 0

    def complete(self, system, user):
        self.calls += 1
        return self.inner.complete(system, user)


def make_attempt(client):
    from ticket_triage.errors import InvalidModelOutput, ServiceError
    from ticket_triage.service import triage

    def attempt(ticket):
        counter = CountingClient(client)
        try:
            decision = triage(ticket, counter)
        except InvalidModelOutput as error:
            return {"kind": "invalid", "raw": error.raw_reply, "calls": counter.calls}
        except ServiceError:
            return {"kind": "service_error", "calls": counter.calls}
        return {"kind": "decision", "decision": decision, "calls": counter.calls}

    return attempt


def run_evaluation(cases, client, sleep=time.sleep, progress=None):
    """Evaluate every case exactly once (with service-error retries). Returns the results."""
    attempt = make_attempt(client)
    results = []
    for case in cases:
        result = evaluator.evaluate_case(case, attempt, sleep=sleep)
        results.append(result)
        if progress:
            progress(result)
    return results


# --------------------------------------------------------------------------------------
# Evidence
# --------------------------------------------------------------------------------------


def jsonable(result):
    data = dict(result)
    score = data.pop("score")
    data["score"] = None if score is None else {"exact": str(score), "decimal": float(score)}
    return data


def sha256_of(paths):
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def generation_files():
    files = sorted(p for p in (ROOT / "src" / "ticket_triage").rglob("*.py") if "__pycache__" not in p.parts)
    prompts = ROOT / "prompts"
    if prompts.exists():
        files += sorted(p for p in prompts.rglob("*") if p.is_file())
    return files


def git_commit():
    try:
        done = subprocess.run(  # noqa: S603, S607 - fixed git command
            ["git", "rev-parse", "HEAD"], cwd=str(ROOT), capture_output=True, text=True, timeout=30, check=False
        )
        return done.stdout.strip() if done.returncode == 0 else "unavailable"
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def package_version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def next_run_number():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    numbers = [int(m.group(1)) for p in RESULTS_DIR.glob("eval-*.json") if (m := re.match(r"eval-(\d+)\.json$", p.name))]
    return max(numbers, default=0) + 1


def clip(text, limit=MAX_TEXT):
    text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
    return text if len(text) <= limit else text[:limit] + f"... [{len(text)} characters in total]"


def gold_summary(case):
    gold = {"action": case["gold_action"]}
    for key in ("gold_category", "gold_priority", "key_terms", "gold_refusal_reason", "forbidden_terms"):
        if key in case:
            gold[key] = case[key]
    return gold


def feedback_markdown(number, label, summary, results, cases):
    by_id = {c["id"]: c for c in cases}
    failing = [r for r in results if r["status"] == "FAIL" or r["guardrail_ok"] is False]
    if summary["result"] == "FAIL" and Fraction(summary["aggregate_exact"]) < evaluator.THRESHOLD:
        weak = sorted((r for r in results if r["status"] == "PASS" and r["score"] < 1), key=lambda r: r["score"])
        failing += [r for r in weak if r not in failing]
    lines = [
        f"# Evaluation feedback for run {number:02d}" + (f" ({label})" if label else ""),
        "",
        "The independent evaluation of the Support Ticket Triage Assistant did not pass.",
        f"Result: {summary['result']}. Aggregate score {summary['aggregate_exact']} "
        f"(about {summary['aggregate']:.4f}); the declared threshold is {summary['threshold_exact']}.",
        "",
        "Rules for this repair:",
        "- Change only files under `src/ticket_triage/` and `prompts/`.",
        "- Do not modify the specification, plan, tasks, constitution, `tests/`, `evals/` or `.harness/`.",
        "- Do not remove or alter evaluation cases, change expected results, lower the threshold, or disable guardrails or checks.",
        "- Do not paste the evaluation tickets or their answers into the prompt; fix the instructions generally.",
        "- Do not open, read, print or modify any .env file. Do not add dependencies or configuration files.",
        "- Preserve behaviour that already passes. Make only the changes the findings require.",
        "",
        f"Cases needing attention: {len(failing)}"
        + (f" (showing the first {MAX_FEEDBACK_CASES})" if len(failing) > MAX_FEEDBACK_CASES else ""),
        "",
    ]
    for result in failing[:MAX_FEEDBACK_CASES]:
        case = by_id[result["id"]]
        score = "n/a" if result["score"] is None else str(result["score"])
        lines += [
            f"## Case {result['id']} ({result['status']}, score {score})",
            f"- Tags: {', '.join(result['tags'])}",
            f"- Input ({len(evaluator.expand_input(case))} characters): `{clip(evaluator.expand_input(case)).encode('unicode_escape').decode('ascii')}`",
            f"- Gold: {clip(gold_summary(case))}",
        ]
        if result["outcome"] == "invalid":
            lines += ["- The application rejected the model reply as invalid. Raw reply:", "", "~~~text", clip(result["raw_reply"]), "~~~", ""]
        elif result["decision"] is not None:
            lines.append(f"- Application output: `{clip(result['decision'])}`")
        if result["guardrail_ok"] is False and not result["violations"]:
            lines.append("- Guardrail not met: priority is more than one level from gold.")
        if result["details"]:
            lines.append(f"- Score details: {clip(result['details'])}")
        for violation in result["violations"]:
            where = f" field `{violation['field']}`" if violation.get("field") else ""
            lines.append(f"- Failed check [{violation['id']}] ({violation['requirement']}){where}: {violation['message']}")
        lines.append("")
    return "\n".join(lines) + "\n"


def write_evidence(number, record, feedback):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    text = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    (RESULTS_DIR / f"eval-{number:02d}.json").write_text(text, encoding="utf-8")
    LATEST.write_text(text, encoding="utf-8")
    if feedback:
        (RESULTS_DIR / f"eval-{number:02d}-feedback.md").write_text(feedback, encoding="utf-8")


def print_summary(number, label, summary, results):
    print(f"\nEvaluation run {number:02d}" + (f" ({label})" if label else ""))
    print("-" * 72)
    print(f"{'case':<42}{'status':<8}{'score':<9}{'attempts'}")
    for r in results:
        score = "-" if r["score"] is None else f"{float(r['score']):.3f}"
        print(f"{r['id'][:40]:<42}{r['status']:<8}{score:<9}{r['attempts']}")
    print("-" * 72)
    print(f"cases {summary['cases']}, scored {summary['scored']}, errors {len(summary['error_cases'])}")
    print(f"aggregate {summary['aggregate_exact']} ({summary['aggregate']:.4f}), threshold {summary['threshold_exact']}")
    print(f"contract and invariants ok: {summary['contract_and_invariants_ok']}; guardrails ok: {summary['guardrails_ok']}")
    print("RESULT: " + summary["result"])
    if summary["result"] == "INVALID":
        print("Service errors are not code failures. Check the key, model name and network, then run again.")
    print(f"Evidence: evidence/eval-results/eval-{number:02d}.json")


def main():
    parser = argparse.ArgumentParser(description="Independent evaluation harness (Part 1B)")
    parser.add_argument("--label", default="", help="short note stored with the run, e.g. initial-generation")
    args = parser.parse_args()

    load_env_file(ROOT / ".env")
    missing = [name for name in ("OPENAI_API_KEY", "OPENAI_MODEL") if not os.environ.get(name, "").strip()]
    if missing:
        print("Missing configuration: " + ", ".join(missing) + " (set it in .env or the environment).")
        return 2

    cases = evaluator.load_dataset(DATASET)
    problems = evaluator.validate_dataset(cases)
    if problems:
        print("The dataset does not satisfy the specification:")
        for problem in problems:
            print("  - " + problem)
        return 2

    from ticket_triage.openai_client import OpenAIClient

    def progress(result):
        score = "-" if result["score"] is None else f"{float(result['score']):.3f}"
        print(f"  {result['id']:<40}{result['status']:<7}{score}", flush=True)

    print(f"Running {len(cases)} cases with model {os.environ['OPENAI_MODEL'].strip()} ...")
    results = run_evaluation(cases, OpenAIClient(), progress=progress)
    summary = evaluator.aggregate(results)
    number = next_run_number()
    record = {
        "run": number,
        "label": args.label,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": summary,
        "configuration": {
            "model": os.environ["OPENAI_MODEL"].strip(),
            "provider": "openai",
            "temperature": "not set (provider default)",
            "attempts_per_case_max": evaluator.MAX_ATTEMPTS,
            "threshold": evaluator.THRESHOLD.__str__(),
        },
        "environment": {
            "python": sys.version.split()[0],
            "openai_package": package_version("openai"),
            "git_commit": git_commit(),
            "generation_sha256": sha256_of(generation_files()),
            "dataset_sha256": sha256_of([DATASET]),
        },
        "cases": [jsonable(r) for r in results],
    }
    feedback = feedback_markdown(number, args.label, summary, results, cases) if summary["result"] == "FAIL" else None
    write_evidence(number, record, feedback)
    print_summary(number, args.label, summary, results)
    return {"PASS": 0, "FAIL": 1, "INVALID": 3}[summary["result"]]


if __name__ == "__main__":
    sys.exit(main())
