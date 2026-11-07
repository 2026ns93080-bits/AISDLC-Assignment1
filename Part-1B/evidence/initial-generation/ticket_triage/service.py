from .contract import parse_decision
from .guard import guard_input
from .model_client import ModelClient
from .openai_client import OpenAIClient
from .prompts import load_system_prompt


def triage(
    ticket_text: str, client: ModelClient | None = None
) -> dict[str, str | None]:
    guarded_decision = guard_input(ticket_text)
    if guarded_decision is not None:
        return guarded_decision

    model_client = client if client is not None else OpenAIClient()
    raw_reply = model_client.complete(
        system=load_system_prompt(),
        user=ticket_text,
    )
    return parse_decision(raw_reply)
