import json
import sys
from pathlib import Path

from .errors import InvalidModelOutput, ServiceError
from .model_client import ModelClient
from .service import triage


def main(argv: list[str], client: ModelClient | None = None) -> int:
    if len(argv) != 1:
        sys.stderr.buffer.write(
            b"error: expected exactly one input file path\n"
        )
        return 2

    try:
        ticket_text = Path(argv[0]).read_bytes().decode("utf-8", errors="strict")
    except (OSError, ValueError):
        sys.stderr.buffer.write(b"error: cannot read input file\n")
        return 2

    if ticket_text.startswith("\ufeff"):
        ticket_text = ticket_text[1:]

    try:
        decision = triage(ticket_text, client=client)
    except ServiceError:
        sys.stderr.buffer.write(b"error: model service unavailable\n")
        return 3
    except InvalidModelOutput:
        sys.stderr.buffer.write(b"error: model returned an invalid response\n")
        return 4

    output = json.dumps(
        decision,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    sys.stdout.buffer.write(output.encode("utf-8") + b"\n")
    return 0
