"""OpenAI adapter tests. Human-owned.

Derived from specs/001-support-ticket-triage/spec.md (AC-019, AC-020, AC-050, AC-051, FR-010)
and the plan's adapter decisions. The real ``openai.OpenAI`` class is replaced with a fake, so
no test here uses the network or a real key. Constructing the real class counts as a failure.
"""

import openai
import pytest
from helpers import (
    T,
    fake_openai_module,
    forbid_openai_client,
    http_library,
    install_openai_factory,
)

from ticket_triage.errors import ServiceError
from ticket_triage.openai_client import OpenAIClient
from ticket_triage.service import triage

FIXED_MESSAGE = "Model service unavailable."
KEY = "test-key-sentinel-0123456789"
MODEL = "test-model-name"
UNDERLYING_TEXT = "SECRET-UNDERLYING-DETAIL"


def configure(monkeypatch, key=KEY, model=MODEL):
    for name, value in (("OPENAI_API_KEY", key), ("OPENAI_MODEL", model)):
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)


def sdk_errors():
    http = http_library()
    request = http.Request("POST", "https://api.openai.com/v1/chat/completions")
    return {
        "timeout": openai.APITimeoutError(request=request),
        "auth": openai.AuthenticationError(
            UNDERLYING_TEXT, response=http.Response(401, request=request), body=None
        ),
        "rate_limit": openai.RateLimitError(
            UNDERLYING_TEXT, response=http.Response(429, request=request), body=None
        ),
        "connection": openai.APIConnectionError(message=UNDERLYING_TEXT, request=request),
    }


# --------------------------------------------------------------------------------------
# AC-050, AC-051: missing or empty configuration, no network request
# --------------------------------------------------------------------------------------

MISSING_KEY = [("unset", None), ("empty", ""), ("blank", "   ")]
MISSING_MODEL = [("unset", None), ("empty", ""), ("blank", "   ")]


@pytest.mark.parametrize(("label", "key"), MISSING_KEY, ids=[f"AC-050-{m[0]}" for m in MISSING_KEY])
def test_ac050_missing_key_raises_service_error_without_network(monkeypatch, label, key):
    configure(monkeypatch, key=key)
    forbid_openai_client(monkeypatch)
    with pytest.raises(ServiceError) as caught:
        OpenAIClient().complete("system", "user")
    assert str(caught.value) == FIXED_MESSAGE


@pytest.mark.parametrize(("label", "model"), MISSING_MODEL, ids=[f"AC-051-{m[0]}" for m in MISSING_MODEL])
def test_ac051_missing_model_raises_service_error_without_network(monkeypatch, label, model):
    configure(monkeypatch, model=model)
    forbid_openai_client(monkeypatch)
    with pytest.raises(ServiceError) as caught:
        OpenAIClient().complete("system", "user")
    assert str(caught.value) == FIXED_MESSAGE


@pytest.mark.parametrize("variable", ["OPENAI_API_KEY", "OPENAI_MODEL"])
def test_ac050_ac051_default_client_path_through_triage(monkeypatch, variable):
    configure(monkeypatch)
    monkeypatch.delenv(variable, raising=False)
    forbid_openai_client(monkeypatch)
    with pytest.raises(ServiceError) as caught:
        triage("My invoice is wrong.", None)
    assert str(caught.value) == FIXED_MESSAGE


# --------------------------------------------------------------------------------------
# AC-019, AC-020 and FR-010: service failures become the fixed ServiceError
# --------------------------------------------------------------------------------------

FAILURES = ["timeout", "auth", "rate_limit", "connection"]
FAILURE_IDS = {"timeout": "AC-019-timeout", "auth": "AC-020-auth"}


@pytest.mark.parametrize("failure", FAILURES, ids=[FAILURE_IDS.get(f, f"FR-010-{f}") for f in FAILURES])
def test_service_failure_raises_fixed_service_error(monkeypatch, failure):
    configure(monkeypatch)
    install_openai_factory(monkeypatch, fake_openai_module(error=sdk_errors()[failure]))
    with pytest.raises(ServiceError) as caught:
        OpenAIClient().complete("system", "user")
    error = caught.value
    assert str(error) == FIXED_MESSAGE
    assert KEY not in str(error) and KEY not in repr(error)
    assert UNDERLYING_TEXT not in str(error) and UNDERLYING_TEXT not in repr(error)
    assert error.__cause__ is None, "the underlying error must not be chained"
    assert error.__context__ is None or error.__suppress_context__, (
        "the underlying error must be hidden (raise ... from None), not implicitly chained"
    )


def test_fr010_service_error_survives_the_full_triage_path(monkeypatch):
    configure(monkeypatch)
    install_openai_factory(monkeypatch, fake_openai_module(error=sdk_errors()["auth"]))
    with pytest.raises(ServiceError) as caught:
        triage("My invoice is wrong.", OpenAIClient())
    assert str(caught.value) == FIXED_MESSAGE


def test_fr010_service_error_text_is_constant():
    assert str(ServiceError()) == FIXED_MESSAGE


def test_plan_non_sdk_exceptions_are_not_swallowed(monkeypatch):
    configure(monkeypatch)
    install_openai_factory(monkeypatch, fake_openai_module(error=RuntimeError("programming error")))
    with pytest.raises(RuntimeError):
        OpenAIClient().complete("system", "user")


# --------------------------------------------------------------------------------------
# Plan decisions: how the request is made
# --------------------------------------------------------------------------------------


def test_plan_request_parameters(monkeypatch):
    configure(monkeypatch)
    fake = fake_openai_module(content=T)
    install_openai_factory(monkeypatch, fake)
    assert OpenAIClient().complete("SYSTEM TEXT", "USER TEXT") == T
    assert len(fake.instances) == 1
    instance = fake.instances[0]
    assert instance.init_kwargs.get("api_key") == KEY
    assert instance.init_kwargs.get("timeout") == 30.0
    assert instance.init_kwargs.get("max_retries") == 0
    request = instance.create_kwargs
    assert request["model"] == MODEL
    assert request["messages"] == [
        {"role": "system", "content": "SYSTEM TEXT"},
        {"role": "user", "content": "USER TEXT"},
    ]
    assert request["response_format"] == {"type": "json_object"}
    assert "temperature" not in request


def test_plan_environment_is_read_at_call_time(monkeypatch):
    configure(monkeypatch, key=None, model=None)
    fake = fake_openai_module(content=T)
    install_openai_factory(monkeypatch, fake)
    client = OpenAIClient()  # constructing it must not require configuration
    configure(monkeypatch)
    assert client.complete("s", "u") == T


def test_plan_null_content_becomes_an_empty_string(monkeypatch):
    configure(monkeypatch)
    install_openai_factory(monkeypatch, fake_openai_module(content=None))
    assert OpenAIClient().complete("s", "u") == ""

