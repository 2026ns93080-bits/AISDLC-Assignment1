import json
import re
from typing import Any

from .errors import InvalidModelOutput

_REQUIRED_KEYS = {
    "action",
    "category",
    "priority",
    "summary",
    "clarification_question",
    "refusal_reason",
}
_CATEGORIES = {"billing", "technical", "account_access", "shipping", "other"}
_PRIORITIES = {"low", "medium", "high", "urgent"}
_REFUSAL_REASONS = {"invalid_input", "prompt_injection", "not_a_support_ticket"}
_DIGIT_RUN = re.compile(r"[0-9]{13,}")
_API_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{20,}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key.")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"Non-standard JSON constant: {value}")


def _has_prohibited_text(value: str) -> bool:
    digits_without_separators = value.replace(" ", "").replace("-", "")
    return (
        _DIGIT_RUN.search(digits_without_separators) is not None
        or _API_KEY_PATTERN.search(value) is not None
        or "OPENAI_API_KEY" in value
    )


def _valid_decision(decision: Any) -> bool:
    if not isinstance(decision, dict) or set(decision) != _REQUIRED_KEYS:
        return False

    action = decision["action"]
    category = decision["category"]
    priority = decision["priority"]
    summary = decision["summary"]
    question = decision["clarification_question"]
    refusal_reason = decision["refusal_reason"]

    if not isinstance(action, str):
        return False

    if action == "triage":
        if (
            not isinstance(category, str)
            or category not in _CATEGORIES
            or not isinstance(priority, str)
            or priority not in _PRIORITIES
            or not isinstance(summary, str)
            or not 1 <= len(summary) <= 200
            or question is not None
            or refusal_reason is not None
        ):
            return False
    elif action == "clarify":
        if (
            category is not None
            or priority is not None
            or summary is not None
            or not isinstance(question, str)
            or not 5 <= len(question) <= 200
            or not question.endswith("?")
            or refusal_reason is not None
        ):
            return False
    elif action == "refuse":
        if (
            category is not None
            or priority is not None
            or summary is not None
            or question is not None
            or not isinstance(refusal_reason, str)
            or refusal_reason not in _REFUSAL_REASONS - {"invalid_input"}
        ):
            return False
    else:
        return False

    return not any(
        _has_prohibited_text(value)
        for value in decision.values()
        if isinstance(value, str)
    )


def parse_decision(raw_reply: str) -> dict[str, str | None]:
    try:
        decision = json.loads(
            raw_reply,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (ValueError, RecursionError):
        raise InvalidModelOutput(raw_reply) from None

    if not _valid_decision(decision):
        raise InvalidModelOutput(raw_reply)

    return decision
