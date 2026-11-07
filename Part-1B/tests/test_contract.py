"""Contract tests: every way a model reply can be invalid, and the boundaries. Human-owned.

Derived from specs/001-support-ticket-triage/spec.md (AC-008..AC-018, AC-030..AC-035,
AC-046..AC-049, AC-056, INV-001..INV-007). Replies are scripted with a fake model and sent
through the public ``triage`` function. Test ids carry the acceptance-criterion id.
"""

import json

import pytest
from helpers import C, P, R, S, T, FakeClient, as_decision, with_field, with_summary

from ticket_triage.errors import InvalidModelOutput
from ticket_triage.service import triage

TICKET = "My invoice is wrong."

FENCED = "```json\n" + T + "\n```"
T_WITH_EXTRA_KEY = T[:-1] + ',"extra":true}'
T_WITH_DUPLICATE_KEY = T[:-1] + ',"action":"triage"}'
T_WITHOUT_LAST_KEY = T.replace(',"refusal_reason":null', "")
CLARIFY_SHORT = with_field("clarification_question", "Help", base=C)
CLARIFY_201 = with_field("clarification_question", "x" * 200 + "?", base=C)
REFUSE_INVALID_INPUT = with_field("refusal_reason", "invalid_input", base=P)

# (id, raw reply) pairs that MUST raise InvalidModelOutput carrying the exact raw reply.
INVALID_REPLIES = [
    ("AC-008", "not-json"),
    ("AC-009", "[]"),
    ("AC-010", T_WITH_EXTRA_KEY),
    ("AC-011", with_field("category", "misc")),
    ("AC-012", with_summary(None)),
    ("AC-013", with_summary("x" * 201)),
    ("AC-014", with_summary("Card 4111111111111111")),
    ("AC-015", FENCED),
    ("AC-016", REFUSE_INVALID_INPUT),
    ("AC-017", with_summary("Refund request sk-abcdefghijklmnopqrstuv")),
    ("AC-018", with_summary("Refund request OPENAI_API_KEY")),
    ("AC-030", T_WITHOUT_LAST_KEY),
    ("AC-031", with_field("category", 7)),
    ("AC-032", with_field("action", "route")),
    ("AC-033", CLARIFY_SHORT),
    ("AC-034", CLARIFY_201),
    ("AC-035", with_summary("Card 4111-1111 1111-1111")),
    ("AC-047", with_summary("Order 1234567890123 delayed")),
    ("AC-049", with_summary("Refund request sk-abcdefghijklmnopqrst")),
    ("AC-056", T_WITH_DUPLICATE_KEY),
]


@pytest.mark.parametrize(("ac", "raw"), INVALID_REPLIES, ids=[i[0] for i in INVALID_REPLIES])
def test_invalid_reply_raises_with_exact_raw_reply(ac, raw):
    client = FakeClient(reply=raw)
    with pytest.raises(InvalidModelOutput) as caught:
        triage(TICKET, client)
    assert caught.value.raw_reply == raw, f"{ac}: raw reply was not preserved exactly"
    assert len(client.calls) == 1, f"{ac}: the model must be called exactly once"


# (id, raw reply) pairs that MUST be returned unchanged.
VALID_REPLIES = [
    ("AC-046", with_summary("Order 123456789012 delayed")),
    ("AC-048", with_summary("Refund request sk-abcdefghijklmnopqrs")),
]


@pytest.mark.parametrize(("ac", "raw"), VALID_REPLIES, ids=[i[0] for i in VALID_REPLIES])
def test_boundary_reply_is_returned_unchanged(ac, raw):
    assert triage(TICKET, FakeClient(reply=raw)) == as_decision(raw), f"{ac}: decision was altered"


@pytest.mark.parametrize("raw", [T, C, R, P, S], ids=["T", "C", "R", "P", "S"])
def test_spec_replies_are_valid(raw):
    assert triage(TICKET, FakeClient(reply=raw)) == as_decision(raw)


# --------------------------------------------------------------------------------------
# INV-001..INV-007 boundaries beyond the numbered criteria
# --------------------------------------------------------------------------------------

CATEGORY_VALUES = ["billing", "technical", "account_access", "shipping", "other"]
PRIORITY_VALUES = ["low", "medium", "high", "urgent"]


@pytest.mark.parametrize("category", CATEGORY_VALUES)
@pytest.mark.parametrize("priority", PRIORITY_VALUES)
def test_inv002_every_category_and_priority_is_accepted(category, priority):
    raw = with_field("priority", priority, base=with_field("category", category))
    assert triage(TICKET, FakeClient(reply=raw)) == as_decision(raw)


@pytest.mark.parametrize("priority", ["critical", "", "MEDIUM", 1, True, ["low"]])
def test_inv002_unsupported_priority_is_rejected(priority):
    raw = with_field("priority", priority)
    with pytest.raises(InvalidModelOutput) as caught:
        triage(TICKET, FakeClient(reply=raw))
    assert caught.value.raw_reply == raw


@pytest.mark.parametrize("value", [True, ["billing"], {"a": 1}, "Billing", ""])
def test_inv002_category_must_be_an_exact_enum_string(value):
    raw = with_field("category", value)
    with pytest.raises(InvalidModelOutput):
        triage(TICKET, FakeClient(reply=raw))


def test_inv003_triage_requires_category_priority_and_summary():
    for field in ("category", "priority", "summary"):
        with pytest.raises(InvalidModelOutput):
            triage(TICKET, FakeClient(reply=with_field(field, None)))


def test_inv003_triage_must_not_carry_clarification_or_refusal_fields():
    with pytest.raises(InvalidModelOutput):
        triage(TICKET, FakeClient(reply=with_field("clarification_question", "Which order?")))
    with pytest.raises(InvalidModelOutput):
        triage(TICKET, FakeClient(reply=with_field("refusal_reason", "prompt_injection")))


def test_inv003_clarify_must_not_carry_triage_fields():
    for field, value in (("category", "billing"), ("priority", "low"), ("summary", "Some summary")):
        with pytest.raises(InvalidModelOutput):
            triage(TICKET, FakeClient(reply=with_field(field, value, base=C)))


def test_inv003_refuse_requires_a_reason_and_no_other_fields():
    with pytest.raises(InvalidModelOutput):
        triage(TICKET, FakeClient(reply=with_field("refusal_reason", None, base=R)))
    with pytest.raises(InvalidModelOutput):
        triage(TICKET, FakeClient(reply=with_field("summary", "Not allowed here", base=R)))


def test_inv004_summary_length_boundaries():
    assert triage(TICKET, FakeClient(reply=with_summary("x" * 200)))["summary"] == "x" * 200
    assert triage(TICKET, FakeClient(reply=with_summary("x")))["summary"] == "x"
    with pytest.raises(InvalidModelOutput):
        triage(TICKET, FakeClient(reply=with_summary("")))


def test_inv004_clarification_question_boundaries():
    shortest = with_field("clarification_question", "Why??", base=C)  # 5 characters
    longest = with_field("clarification_question", "x" * 199 + "?", base=C)  # 200 characters
    assert triage(TICKET, FakeClient(reply=shortest))["clarification_question"] == "Why??"
    assert len(triage(TICKET, FakeClient(reply=longest))["clarification_question"]) == 200
    for bad in ("Whys", "What is the problem", "x" * 200, "Is this ok? yes"):
        raw = with_field("clarification_question", bad, base=C)
        with pytest.raises(InvalidModelOutput):
            triage(TICKET, FakeClient(reply=raw))


def test_inv004_lengths_count_code_points_not_bytes():
    assert triage(TICKET, FakeClient(reply=with_summary("\u00e9" * 200)))["summary"] == "\u00e9" * 200
    with pytest.raises(InvalidModelOutput):
        triage(TICKET, FakeClient(reply=with_summary("\u00e9" * 201)))


def test_inv005_digit_runs_ignore_spaces_and_hyphens_and_cover_every_string_field():
    assert triage(TICKET, FakeClient(reply=with_summary("Ref 1234-5678-9012 pending")))
    with pytest.raises(InvalidModelOutput):
        triage(TICKET, FakeClient(reply=with_summary("Ref 1234-5678-9012-3 pending")))
    question_with_digits = with_field("clarification_question", "Is it 1234567890123?", base=C)
    with pytest.raises(InvalidModelOutput):
        triage(TICKET, FakeClient(reply=question_with_digits))


def test_inv006_literal_key_name_is_rejected_in_any_string_field():
    question = with_field("clarification_question", "Is OPENAI_API_KEY set?", base=C)
    with pytest.raises(InvalidModelOutput):
        triage(TICKET, FakeClient(reply=question))


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_fr009_non_standard_json_constants_are_rejected(constant):
    raw = T.replace('"Refund request for duplicate charge."', constant)
    with pytest.raises(InvalidModelOutput) as caught:
        triage(TICKET, FakeClient(reply=raw))
    assert caught.value.raw_reply == raw


@pytest.mark.parametrize("raw", ["", "   ", "null", "true", "7", '"text"', "{", T + " trailing"])
def test_fr009_non_object_or_malformed_replies_are_rejected(raw):
    with pytest.raises(InvalidModelOutput) as caught:
        triage(TICKET, FakeClient(reply=raw))
    assert caught.value.raw_reply == raw


def test_fr009_whitespace_around_valid_json_is_not_repair():
    padded = "\n  " + T + "\n"
    # Valid JSON with surrounding whitespace is still valid JSON; it must parse, not be rewritten.
    assert triage(TICKET, FakeClient(reply=padded)) == json.loads(T)


def test_fr009_nested_duplicate_keys_are_rejected_at_any_depth():
    nested = T[:-1] + ',"extra":{"a":1,"a":2}}'
    with pytest.raises(InvalidModelOutput) as caught:
        triage(TICKET, FakeClient(reply=nested))
    assert caught.value.raw_reply == nested


def test_fr009_deeply_nested_reply_is_an_invalid_output_not_a_crash():
    deep = "[" * 100000 + "]" * 100000
    with pytest.raises(InvalidModelOutput) as caught:
        triage(TICKET, FakeClient(reply=deep))
    assert caught.value.raw_reply == deep
