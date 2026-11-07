def guard_input(text: str) -> dict[str, str | None] | None:
    if text.strip() != "" and len(text) <= 4000:
        return None

    return {
        "action": "refuse",
        "category": None,
        "priority": None,
        "summary": None,
        "clarification_question": None,
        "refusal_reason": "invalid_input",
    }
