#!/usr/bin/env python3
"""Independent deterministic harness for the Support Ticket Triage Assistant (Part 1B).

Owned by the human engineer. The coding agent must not modify anything in .harness/.
This runner checks the deterministic parts (code quality, security, policy, prompt rules,
tests, coverage, traceability). The live model evaluation is a separate command, run_eval.py,
which implements the three-layer evaluation pipeline. No LLM is used here.

Usage (from the Part-1B folder, with the virtual environment active):
    python .harness/run_harness.py --lock             # human, once, before implementation
    python .harness/run_harness.py [--label TEXT]     # run every gate and save evidence

Gates, in order:
    1. integrity     tests/, evals/, .harness/, the spec and the constitution are unchanged
    2. lint          ruff reports zero errors on src/
    3. security      bandit reports zero medium or high severity findings on src/
    4. policy        source follows the constitution and plan (AST checks)
    5. prompt        prompts/system.md defines the contract and contains no evaluation ticket
    6. tests         every automated test passes
    7. coverage      line coverage of src/ticket_triage is at least 90 percent
                     (the thin OpenAI client module is the only exclusion, per the constitution)
    8. traceability  every AC in the spec has a test

Evidence per run (never overwritten):
    evidence/harness-results/run-NN.json      structured result
    evidence/harness-results/run-NN.log       full stdout/stderr of every tool
    evidence/harness-results/run-NN-feedback.md   failure evidence for the coding agent (failed runs)

Exit status: 0 when every gate passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS_DIR = ROOT / ".harness"
SRC_DIR = ROOT / "src"
SRC_PKG = SRC_DIR / "ticket_triage"
TESTS_DIR = ROOT / "tests"
EVALS_DIR = ROOT / "evals"
PROMPT_FILE = ROOT / "prompts" / "system.md"
RESULTS_DIR = ROOT / "evidence" / "harness-results"
LOCK_FILE = HARNESS_DIR / "locked-hashes.json"
COVERAGE_THRESHOLD = 90.0
MAX_FEEDBACK_FINDINGS = 25

LOG_LINES: list[str] = []


# --------------------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------------------


def finding(gate, code, message, location="", expected="", observed=""):
    return {
        "gate": gate,
        "code": code,
        "message": message,
        "location": location,
        "expected": expected,
        "observed": observed,
    }


def gate_result(name, tool, findings, command="", exit_code=None, details=None):
    return {
        "name": name,
        "tool": tool,
        "status": "PASS" if not findings else "FAIL",
        "command": command,
        "exit_code": exit_code,
        "findings": findings,
        "details": details or {},
    }


def run(cmd, extra_env=None, timeout=600):
    """Run a command inside the Part-1A folder and log everything it prints."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if extra_env:
        env.update(extra_env)
    shown = " ".join(str(part) for part in cmd)
    try:
        done = subprocess.run(  # noqa: S603 - fixed commands built by this script
            [str(part) for part in cmd],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        code, out, err = done.returncode, done.stdout, done.stderr
    except subprocess.TimeoutExpired:
        code, out, err = -1, "", f"timed out after {timeout} seconds"
    LOG_LINES.append(f"$ {shown}\n--- exit code: {code}\n--- stdout ---\n{out}\n--- stderr ---\n{err}\n")
    return code, out, err


def normalised_digest(path):
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def protected_files():
    """Files the coding agent must never change."""
    files = []
    for base in (TESTS_DIR, EVALS_DIR, HARNESS_DIR):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            if path == LOCK_FILE or path.name.startswith(".coverage"):
                continue
            files.append(path)
    files += sorted((ROOT / "specs").glob("*/spec.md"))
    constitution = ROOT / ".specify" / "memory" / "constitution.md"
    if constitution.exists():
        files.append(constitution)
    return files


def source_files():
    if not SRC_PKG.exists():
        return []
    return sorted(p for p in SRC_PKG.rglob("*.py") if "__pycache__" not in p.parts)


def prompt_files():
    folder = ROOT / "prompts"
    return sorted(p for p in folder.rglob("*") if p.is_file()) if folder.exists() else []


def source_tree_digest():
    """Hash of everything the coding agent may change: src/ticket_triage and prompts/."""
    digest = hashlib.sha256()
    for path in source_files() + prompt_files():
        digest.update(rel(path).encode("utf-8"))
        digest.update(normalised_digest(path).encode("ascii"))
    return digest.hexdigest()


def tool_version(args):
    code, out, err = run([sys.executable, "-m", *args])
    text = (out or err).strip().splitlines()
    return text[0] if text else f"unavailable (exit {code})"


# --------------------------------------------------------------------------------------
# Gate 1: integrity
# --------------------------------------------------------------------------------------


def lock_hashes():
    files = {rel(p): normalised_digest(p) for p in protected_files()}
    payload = {
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "SHA-256 of files the coding agent must not change. Re-lock only by a deliberate "
        "human decision and record the reason in evidence/spec-change-log.md.",
        "files": files,
    }
    LOCK_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Locked {len(files)} protected files in {rel(LOCK_FILE)}")
    for name in files:
        print(f"  {name}")


def gate_integrity():
    gate = "integrity"
    if not LOCK_FILE.exists():
        return gate_result(
            gate,
            "sha256",
            [
                finding(
                    gate,
                    "LOCK_MISSING",
                    "No hash lock found. Run: python .harness/run_harness.py --lock",
                    rel(LOCK_FILE),
                )
            ],
        )
    locked = json.loads(LOCK_FILE.read_text(encoding="utf-8"))["files"]
    current = {rel(p): normalised_digest(p) for p in protected_files()}
    findings = []
    for name, digest in locked.items():
        if name not in current:
            findings.append(
                finding(gate, "PROTECTED_FILE_MISSING", "Protected file was deleted.", name, "present", "missing")
            )
        elif current[name] != digest:
            findings.append(
                finding(gate, "PROTECTED_FILE_CHANGED", "Protected file was modified.", name, "unchanged", "modified")
            )
    for name in current:
        if name not in locked:
            findings.append(
                finding(gate, "PROTECTED_FILE_ADDED", "New file in a protected area.", name, "not present", "added")
            )
    return gate_result(gate, "sha256", findings, details={"files_checked": len(locked)})


# --------------------------------------------------------------------------------------
# Gate 2: lint (ruff)
# --------------------------------------------------------------------------------------


def src_missing_finding(gate):
    return finding(
        gate, "SRC_MISSING", "src/ticket_triage does not exist yet.", "src/ticket_triage", "package present", "missing"
    )


def gate_lint():
    gate = "lint"
    if not SRC_PKG.exists():
        return gate_result(gate, "ruff", [src_missing_finding(gate)])
    cmd = [
        sys.executable, "-m", "ruff", "check",
        "--config", ".harness/ruff.toml", "--no-cache", "--output-format", "json", "src",
    ]  # fmt: skip
    code, out, err = run(cmd)
    findings = []
    try:
        results = json.loads(out) if out.strip() else []
    except json.JSONDecodeError:
        results = None
    if results is None or code not in (0, 1):
        findings.append(
            finding(gate, "RUFF_ERROR", "ruff did not produce a usable result.", observed=(err or out)[:500])
        )
    else:
        for item in results:
            location = f"{Path(item['filename']).name}:{item['location']['row']}"
            findings.append(
                finding(gate, f"RUFF_{item['code']}", item["message"], location, "no ruff errors", item["code"])
            )
    return gate_result(gate, "ruff", findings, " ".join(cmd[2:]), code, {"violations": len(findings)})


# --------------------------------------------------------------------------------------
# Gate 3: security (bandit)
# --------------------------------------------------------------------------------------


def gate_security():
    gate = "security"
    if not SRC_PKG.exists():
        return gate_result(gate, "bandit", [src_missing_finding(gate)])
    cmd = [sys.executable, "-m", "bandit", "-r", "src", "-f", "json", "-q"]
    code, out, err = run(cmd)
    findings = []
    low = 0
    try:
        report = json.loads(out)
    except json.JSONDecodeError:
        report = None
    if report is None:
        findings.append(
            finding(gate, "BANDIT_ERROR", "bandit did not produce a usable result.", observed=(err or out)[:500])
        )
    else:
        for item in report.get("results", []):
            severity = item.get("issue_severity", "").upper()
            if severity in ("MEDIUM", "HIGH"):
                location = f"{Path(item['filename']).name}:{item['line_number']}"
                findings.append(
                    finding(
                        gate,
                        f"BANDIT_{item['test_id']}",
                        item["issue_text"],
                        location,
                        "no medium or high severity findings",
                        f"{severity} severity",
                    )
                )
            else:
                low += 1
        for problem in report.get("errors", []):
            findings.append(finding(gate, "BANDIT_FILE_ERROR", str(problem)[:300]))
    return gate_result(gate, "bandit", findings, " ".join(cmd[2:]), code, {"low_severity_ignored": low})


# --------------------------------------------------------------------------------------
# Gate 4: policy (AST checks derived from the constitution and plan)
# --------------------------------------------------------------------------------------

ADAPTER_MODULE = "openai_client.py"
ENVIRONMENT_MODULES = {"openai_client.py", "env_loader.py", "__main__.py"}
DOT_ENV_MODULES = {"env_loader.py", "__main__.py"}
KEY_LITERAL = re.compile(r"sk-[A-Za-z0-9_-]{20,}")

FORBIDDEN_IMPORTS = {
    "argparse": "Plan: no option parser; check len(argv) only (FR-012).",
    "optparse": "Plan: no option parser (FR-012).",
    "getopt": "Plan: no option parser (FR-012).",
    "requests": "Constitution I and V: network access only through the openai package.",
    "urllib": "Constitution I: no network access outside the OpenAI client.",
    "http": "Constitution I: no network access outside the OpenAI client.",
    "socket": "Constitution I: no network access outside the OpenAI client.",
    "ssl": "Constitution I: no network access outside the OpenAI client.",
    "subprocess": "Constitution II: ticket text must never reach a command.",
    "pickle": "Constitution: no unsafe deserialisation.",
    "marshal": "Constitution: no unsafe deserialisation.",
    "shelve": "Constitution: no unsafe deserialisation.",
    "ctypes": "Constitution V: standard library only.",
}
FORBIDDEN_BUILTINS = {
    "eval": "Constitution II: ticket text must never be executed.",
    "exec": "Constitution II: ticket text must never be executed.",
    "print": "Plan: write bytes through sys.stdout.buffer / sys.stderr.buffer (FR-012, FR-013).",
    "__import__": "Constitution: no dynamic imports.",
}
FORBIDDEN_STRINGS = {
    "json_schema": "Plan: JSON mode only, not strict structured outputs, so schema violations stay visible.",
}


def policy_findings_for(path):
    gate = "policy"
    name = path.name
    found = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=name)
    except (SyntaxError, UnicodeDecodeError) as exc:
        return [finding(gate, "POLICY_SYNTAX", f"Cannot parse source: {exc}", name)]

    def add(code, message, node, expected, observed):
        found.append(finding(gate, code, message, f"{name}:{getattr(node, 'lineno', 0)}", expected, observed))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            if isinstance(node, ast.ImportFrom) and node.level > 0:
                continue
            modules = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            for module in modules:
                top = module.split(".")[0]
                if top in FORBIDDEN_IMPORTS:
                    add("POLICY_FORBIDDEN_IMPORT", FORBIDDEN_IMPORTS[top], node, "module not imported", f"import {top}")
                elif top == "openai":
                    if name != ADAPTER_MODULE:
                        add("POLICY_OPENAI_OUTSIDE_ADAPTER", "Constitution I: the openai package is used only in openai_client.py.",
                            node, "no openai import", f"import {top}")  # fmt: skip
                elif top not in sys.stdlib_module_names and top != "ticket_triage":
                    add("POLICY_NON_STDLIB_IMPORT", "Constitution V: openai is the only third-party runtime dependency.", node,
                        "standard library module", f"import {top}")  # fmt: skip
            if isinstance(node, ast.ImportFrom) and node.module == "os" and name not in ENVIRONMENT_MODULES:
                if any(alias.name in ("environ", "getenv") for alias in node.names):
                    add("POLICY_ENV_ACCESS", "Constitution I: only the adapter and the entry point touch the environment.",
                        node, "no environment access", "from os import environ/getenv")  # fmt: skip
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_BUILTINS:
            add("POLICY_FORBIDDEN_NAME", FORBIDDEN_BUILTINS[node.id], node, f"no use of {node.id}", node.id)
        elif isinstance(node, ast.Attribute):
            if node.attr in ("environ", "getenv") and isinstance(node.value, ast.Name) and node.value.id == "os":
                if name not in ENVIRONMENT_MODULES:
                    add("POLICY_ENV_ACCESS", "Constitution I: only the adapter and the entry point touch the environment.",
                        node, "no environment access", f"os.{node.attr}")  # fmt: skip
            if (
                node.attr == "write"
                and isinstance(node.value, ast.Attribute)
                and node.value.attr in ("stdout", "stderr")
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "sys"
            ):
                add("POLICY_TEXT_STREAM_WRITE", "Plan: write bytes to sys.stdout.buffer / sys.stderr.buffer (FR-012).",
                    node, "sys.stdout.buffer.write", f"sys.{node.value.attr}.write")  # fmt: skip
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if KEY_LITERAL.search(node.value):
                add("POLICY_HARDCODED_KEY", "Constitution: no API key may appear in source.", node, "no key literal", "key-like literal")
            for needle, message in FORBIDDEN_STRINGS.items():
                if needle in node.value:
                    add("POLICY_FORBIDDEN_STRING", message, node, f"no {needle!r}", repr(node.value)[:60])
            if node.value.endswith(".env") and name not in DOT_ENV_MODULES:
                add("POLICY_DOT_ENV_IN_LIBRARY", "Constitution I and plan: library modules never read .env.", node,
                    "no .env access", repr(node.value)[:60])  # fmt: skip
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg == "temperature":
                    add("POLICY_TEMPERATURE", "Plan: do not send a temperature parameter.", node, "no temperature", "temperature=...")
                if keyword.arg == "max_retries" and not (isinstance(keyword.value, ast.Constant) and keyword.value.value == 0):
                    add("POLICY_RETRIES", "Plan: max_retries must be 0 so the evaluation controls retries (FR-019).", node,
                        "max_retries=0", "max_retries other than 0")  # fmt: skip
        elif isinstance(node, ast.ExceptHandler):
            blanket = node.type is None or (
                isinstance(node.type, ast.Name) and node.type.id in ("Exception", "BaseException")
            )
            if blanket:
                add("POLICY_BLANKET_EXCEPT", "Plan: handle only expected exception classes; no blanket except.", node,
                    "specific exception classes", "bare or blanket except")  # fmt: skip
    return found


def gate_policy():
    gate = "policy"
    files = source_files()
    if not files:
        return gate_result(gate, "ast", [src_missing_finding(gate)])
    findings = []
    for path in files:
        findings.extend(policy_findings_for(path))
    return gate_result(gate, "ast", findings, details={"files_checked": len(files)})


# --------------------------------------------------------------------------------------
# Gate 5: prompt (feedforward rules for prompts/system.md)
# --------------------------------------------------------------------------------------

REQUIRED_PROMPT_WORDS = [
    "action", "category", "priority", "summary", "clarification_question", "refusal_reason",
    "triage", "clarify", "refuse",
    "billing", "technical", "account_access", "shipping", "other",
    "low", "medium", "high", "urgent",
    "prompt_injection", "not_a_support_ticket",
]  # fmt: skip


def gate_prompt():
    gate = "prompt"
    if not PROMPT_FILE.exists() or not PROMPT_FILE.read_text(encoding="utf-8").strip():
        return gate_result(
            gate, "text", [finding(gate, "PROMPT_MISSING", "prompts/system.md is missing or empty.", "prompts/system.md")]
        )
    text = PROMPT_FILE.read_text(encoding="utf-8")
    lowered = text.lower()
    findings = []
    missing = [word for word in REQUIRED_PROMPT_WORDS if word not in text]
    if missing:
        findings.append(
            finding(gate, "PROMPT_MISSING_TERMS", "The system prompt does not define the full contract.",
                    "prompts/system.md", "all contract terms present", f"missing: {', '.join(missing)}")  # fmt: skip
        )
    if "json" not in lowered:
        findings.append(finding(gate, "PROMPT_NO_JSON", "The prompt must mention JSON (required for JSON mode).", "prompts/system.md"))
    if KEY_LITERAL.search(text):
        findings.append(finding(gate, "PROMPT_KEY_LITERAL", "An API key pattern appears in the prompt.", "prompts/system.md"))
    dataset_path = EVALS_DIR / "dataset.json"
    if dataset_path.exists():
        for case in json.loads(dataset_path.read_text(encoding="utf-8")):
            ticket = case["input"] if isinstance(case["input"], str) else ""
            if len(ticket.strip()) >= 20 and ticket.strip().lower() in lowered:
                findings.append(
                    finding(gate, "PROMPT_CONTAINS_EVAL_CASE", "An evaluation ticket was pasted into the prompt.",
                            "prompts/system.md", "no evaluation ticket text", f"case {case['id']}")  # fmt: skip
                )
    return gate_result(gate, "text", findings, details={"characters": len(text)})


# --------------------------------------------------------------------------------------
# Gates 5 and 6: tests and coverage (pytest, pytest-cov)
# --------------------------------------------------------------------------------------

PYTEST_BASE = [
    "-m", "pytest", "tests", "-c", ".harness/pytest.ini", "--rootdir", ".", "-p", "no:cacheprovider",
]  # fmt: skip


def parse_failure_text(text):
    """Pull the assertion message out of a pytest junit failure body."""
    lines = []
    for line in text.splitlines():
        if line.startswith("E"):
            lines.append(re.sub(r"^E\s{0,3}", "", line).rstrip())
    return lines or text.strip().splitlines()[-5:]


def gate_tests_and_coverage():
    test_gate, cov_gate = "tests", "coverage"
    if not TESTS_DIR.exists():
        failure = finding(test_gate, "TESTS_MISSING", "tests/ does not exist.", "tests")
        return (
            gate_result(test_gate, "pytest", [failure]),
            gate_result(cov_gate, "pytest-cov", [finding(cov_gate, "NO_COVERAGE_DATA", "Tests did not run.")]),
            {},
        )
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        junit = tmp_path / "junit.xml"
        cov_json = tmp_path / "coverage.json"
        cmd = [
            sys.executable, *PYTEST_BASE, "-q", "--tb=short", f"--junitxml={junit}",
            "--cov=src/ticket_triage", "--cov-config=.harness/coveragerc",
            f"--cov-report=json:{cov_json}", "--cov-report=term-missing",
        ]  # fmt: skip
        code, out, err = run(cmd, extra_env={"COVERAGE_FILE": str(tmp_path / ".coverage")})
        test_findings = []
        stats = {"total": 0, "failed": 0, "errors": 0, "skipped": 0}
        if junit.exists():
            root = ET.parse(junit).getroot()
            for case in root.iter("testcase"):
                stats["total"] += 1
                bad = case.find("failure")
                kind = "TEST_FAILED"
                if bad is None:
                    bad = case.find("error")
                    kind = "TEST_ERROR"
                if case.find("skipped") is not None:
                    stats["skipped"] += 1
                if bad is None:
                    continue
                stats["failed" if kind == "TEST_FAILED" else "errors"] += 1
                message_lines = parse_failure_text(bad.text or bad.get("message", ""))
                label = message_lines[0].replace("AssertionError: ", "", 1) if message_lines else ""
                pairs = []
                for line in message_lines[1:]:
                    if ": expected " in line and ", observed " in line:
                        field, rest = line.strip().split(": expected ", 1)
                        want, got = rest.rsplit(", observed ", 1)
                        pairs.append((field, want, got))
                if pairs:
                    message = label
                    expected = "; ".join(f"{field}: {want}" for field, want, _ in pairs)
                    observed = "; ".join(f"{field}: {got}" for field, _, got in pairs)
                else:
                    message = "\n".join(message_lines[:12])
                    expected = "see message"
                    observed = message_lines[-1].strip() if message_lines else ""
                location = f"{case.get('classname', '').replace('.', '/')}.py::{case.get('name', '')}"
                test_findings.append(finding(test_gate, kind, message, location, expected, observed))
        else:
            test_findings.append(
                finding(test_gate, "PYTEST_ERROR", "pytest produced no result file.", observed=(err or out)[-500:])
            )
        if code != 0 and not test_findings:
            test_findings.append(
                finding(test_gate, "PYTEST_EXIT", f"pytest exited with status {code}.", observed=(err or out)[-500:])
            )
        tests_gate = gate_result(test_gate, "pytest", test_findings, " ".join(cmd[1:7]), code, stats)

        cov_findings = []
        percent = None
        if cov_json.exists():
            data = json.loads(cov_json.read_text(encoding="utf-8"))
            percent = round(float(data["totals"]["percent_covered"]), 2)
            if percent < COVERAGE_THRESHOLD:
                weakest = sorted(
                    ((Path(name).name, info["summary"]["percent_covered"], info.get("missing_lines", []))
                     for name, info in data.get("files", {}).items()),
                    key=lambda item: item[1],
                )[:3]  # fmt: skip
                detail = "; ".join(f"{n} {p:.0f}% missing lines {m[:15]}" for n, p, m in weakest)
                cov_findings.append(
                    finding(cov_gate, "COVERAGE_BELOW_THRESHOLD", f"Line coverage is below the gate. {detail}",
                            "src/ticket_triage", f">= {COVERAGE_THRESHOLD}%", f"{percent}%")  # fmt: skip
                )
        else:
            cov_findings.append(
                finding(cov_gate, "NO_COVERAGE_DATA", "No coverage data was produced (tests may not have run).",
                        "src/ticket_triage", f">= {COVERAGE_THRESHOLD}%", "no data")  # fmt: skip
            )
        cov_result = gate_result(cov_gate, "pytest-cov", cov_findings, details={"percent_covered": percent})
    stats["coverage_percent"] = percent
    return tests_gate, cov_result, stats


# --------------------------------------------------------------------------------------
# Gate 7: traceability (AC ids in the spec versus test ids)
# --------------------------------------------------------------------------------------


def spec_acceptance_ids():
    ids = set()
    for spec in sorted((ROOT / "specs").glob("*/spec.md")):
        ids.update(re.findall(r"\*\*AC-(\d{3})\*\*", spec.read_text(encoding="utf-8")))
    return sorted(ids)


def gate_traceability():
    gate = "traceability"
    expected = spec_acceptance_ids()
    if not expected:
        return gate_result(
            gate, "spec+pytest", [finding(gate, "NO_SPEC_ACS", "No AC ids found in specs/*/spec.md.", "specs")]
        )
    cmd = [sys.executable, *PYTEST_BASE, "--collect-only", "-q"]
    code, out, err = run(cmd)
    node_ids = [line.strip() for line in out.splitlines() if "::" in line]
    findings = []
    if code != 0 or not node_ids:
        findings.append(
            finding(gate, "COLLECTION_FAILED", "pytest could not collect the tests.", "tests", "tests collected",
                    (err or out)[-400:])  # fmt: skip
        )
        return gate_result(gate, "spec+pytest", findings, exit_code=code)
    covered = set()
    for node_id in node_ids:
        covered.update(re.findall(r"(?<![A-Za-z])AC[-_]?(\d{3})(?!\d)", node_id, flags=re.IGNORECASE))
    for number in expected:
        if number not in covered:
            findings.append(
                finding(gate, "AC_WITHOUT_TEST", f"AC-{number} is in the spec but no test id mentions it.",
                        f"AC-{number}", "at least one test", "none")  # fmt: skip
            )
    return gate_result(
        gate, "spec+pytest", findings, exit_code=code,
        details={"acs_in_spec": len(expected), "acs_with_tests": len(covered & set(expected)), "tests_collected": len(node_ids)},
    )  # fmt: skip


# --------------------------------------------------------------------------------------
# Evidence writing
# --------------------------------------------------------------------------------------


def next_run_number():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    numbers = [int(m.group(1)) for p in RESULTS_DIR.glob("run-*.json") if (m := re.match(r"run-(\d+)\.json$", p.name))]
    return max(numbers, default=0) + 1


def git_commit():
    code, out, _ = run(["git", "rev-parse", "HEAD"])
    return out.strip() if code == 0 else "unavailable"


def feedback_markdown(number, result):
    failed = [g for g in result["gates"] if g["status"] == "FAIL"]
    items = [f for g in failed for f in g["findings"]]
    lines = [
        f"# Harness feedback for run {number:02d}",
        "",
        "The independent harness rejected the current implementation.",
        "Fix the root cause of each finding below.",
        "",
        "Rules for this repair:",
        "- Change only files under `src/ticket_triage/` and `prompts/`.",
        "- Do not modify `tests/`, `evals/`, `.harness/`, the specification, plan, tasks or constitution.",
        "- Do not weaken, skip or delete any test; do not lower any threshold; do not disable lint or security checks.",
        "- Do not add dependencies, packaging files or configuration files. Do not open, read, print or modify any .env file.",
        "- Preserve behaviour that already passes. Make only the changes the findings require.",
        "",
        "Failed gates: " + ", ".join(g["name"] for g in failed),
        f"Findings: {len(items)}" + (f" (showing the first {MAX_FEEDBACK_FINDINGS})" if len(items) > MAX_FEEDBACK_FINDINGS else ""),
        "",
    ]
    for index, item in enumerate(items[:MAX_FEEDBACK_FINDINGS], start=1):
        lines.append(f"## Finding {index}: [{item['gate']}] {item['code']}")
        if item["location"]:
            lines.append(f"- Where: `{item['location']}`")
        if item["expected"]:
            lines.append(f"- Expected: {item['expected']}")
        if item["observed"]:
            lines.append(f"- Observed: {item['observed']}")
        lines.append("- Evidence:")
        lines.append("")
        lines.append("```text")
        lines.append(item["message"])
        lines.append("```")
        lines.append("")
    return "\n".join(lines) + "\n"


def write_evidence(result):
    number = result["run"]
    base = RESULTS_DIR / f"run-{number:02d}"
    (base.with_suffix(".json")).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (RESULTS_DIR / f"run-{number:02d}.log").write_text("\n".join(LOG_LINES), encoding="utf-8")
    if not result["passed"]:
        (RESULTS_DIR / f"run-{number:02d}-feedback.md").write_text(feedback_markdown(number, result), encoding="utf-8")


def print_summary(result):
    print(f"\nHarness run {result['run']:02d}" + (f" ({result['label']})" if result["label"] else ""))
    print("-" * 60)
    for gate in result["gates"]:
        extra = ""
        if gate["name"] == "tests":
            s = gate["details"]
            extra = f"  {s.get('total', 0)} tests, {s.get('failed', 0)} failed, {s.get('errors', 0)} errors"
        elif gate["name"] == "coverage":
            extra = f"  {gate['details'].get('percent_covered')}% (gate {COVERAGE_THRESHOLD}%)"
        elif gate["findings"]:
            extra = f"  {len(gate['findings'])} finding(s)"
        print(f"{gate['name']:<14}{gate['status']}{extra}")
    print("-" * 60)
    print("RESULT: " + ("PASS" if result["passed"] else "FAIL"))
    print(f"Evidence: evidence/harness-results/run-{result['run']:02d}.json (+ .log" + ("" if result["passed"] else ", -feedback.md") + ")")
    if result["passed"]:
        print("Automated PASS is not acceptance. Now do the human review and record ACCEPT or REJECT.")


def main():
    parser = argparse.ArgumentParser(description="Independent deterministic harness for the Support Ticket Triage Assistant")
    parser.add_argument("--lock", action="store_true", help="record hashes of protected files and exit")
    parser.add_argument("--label", default="", help="short note stored with the run, e.g. initial-generation")
    args = parser.parse_args()

    if args.lock:
        lock_hashes()
        return 0

    gates = [gate_integrity(), gate_lint(), gate_security(), gate_policy(), gate_prompt()]
    tests_gate, coverage_gate, stats = gate_tests_and_coverage()
    gates += [tests_gate, coverage_gate, gate_traceability()]

    result = {
        "run": next_run_number(),
        "label": args.label,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "passed": all(g["status"] == "PASS" for g in gates),
        "gates": gates,
        "summary": stats,
        "environment": {
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "ruff": tool_version(["ruff", "--version"]),
            "bandit": tool_version(["bandit", "--version"]),
            "pytest": tool_version(["pytest", "--version"]),
            "git_commit": git_commit(),
            "src_tree_sha256": source_tree_digest(),
        },
    }
    write_evidence(result)
    print_summary(result)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
