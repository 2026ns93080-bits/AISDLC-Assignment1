"""Shared test helpers. Owned by the human engineer.

The exact replies T, C, R, P and S are copied from the acceptance-criteria preamble of
specs/001-support-ticket-triage/spec.md. Expected values are written out literally; nothing
here is computed with the code under test.
"""

import json
from types import SimpleNamespace

# Exact raw model replies defined in the specification.
T = (
    '{"action":"triage","category":"billing","priority":"medium",'
    '"summary":"Refund request for duplicate charge.","clarification_question":null,'
    '"refusal_reason":null}'
)
C = (
    '{"action":"clarify","category":null,"priority":null,"summary":null,'
    '"clarification_question":"What problem are you experiencing?","refusal_reason":null}'
)
R = (
    '{"action":"refuse","category":null,"priority":null,"summary":null,'
    '"clarification_question":null,"refusal_reason":"not_a_support_ticket"}'
)
P = (
    '{"action":"refuse","category":null,"priority":null,"summary":null,'
    '"clarification_question":null,"refusal_reason":"prompt_injection"}'
)
S = (
    '{"action":"triage","category":"shipping","priority":"medium",'
    '"summary":"My parcel is missing; tracking help is needed.","clarification_question":null,'
    '"refusal_reason":null}'
)

INVALID_INPUT_DECISION = {
    "action": "refuse",
    "category": None,
    "priority": None,
    "summary": None,
    "clarification_question": None,
    "refusal_reason": "invalid_input",
}

TICKET = "My invoice is wrong."


def as_decision(raw):
    """The six values of a raw reply, as a dictionary."""
    return json.loads(raw)


def with_summary(summary, base=T):
    """Raw reply equal to ``base`` except for the summary value."""
    data = json.loads(base)
    data["summary"] = summary
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def with_field(name, value, base=T):
    """Raw reply equal to ``base`` except for one field value."""
    data = json.loads(base)
    data[name] = value
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


class FakeClient:
    """Model double: returns a fixed reply (or raises) and records every call."""

    def __init__(self, reply=None, error=None):
        self.reply = reply
        self.error = error
        self.calls = []

    def complete(self, system, user):
        self.calls.append((system, user))
        if self.error is not None:
            raise self.error
        return self.reply


def fake_openai_module(content="{}", error=None):
    """A stand-in for ``openai.OpenAI`` that records how it is constructed and called."""

    class FakeOpenAI:
        instances = []

        def __init__(self, **kwargs):
            self.init_kwargs = kwargs
            self.create_kwargs = None
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
            FakeOpenAI.instances.append(self)

        def _create(self, **kwargs):
            self.create_kwargs = kwargs
            if error is not None:
                raise error
            message = SimpleNamespace(content=content)
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    return FakeOpenAI


def forbid_openai_client(monkeypatch):
    """Make any construction of the real OpenAI client fail the test (proves no network use)."""

    def refuse(**_kwargs):
        raise AssertionError("an OpenAI client was constructed")

    install_openai_factory(monkeypatch, refuse)


def install_openai_factory(monkeypatch, factory):
    """Replace ``openai.OpenAI`` everywhere the application could have bound it."""
    import openai

    monkeypatch.setattr(openai, "OpenAI", factory)
    import ticket_triage.openai_client as adapter

    if hasattr(adapter, "OpenAI"):
        monkeypatch.setattr(adapter, "OpenAI", factory)


def http_library():
    """The HTTP library the installed openai package uses (httpx2 in newer releases)."""
    try:
        import httpx2 as library
    except ImportError:
        import httpx as library
    return library
