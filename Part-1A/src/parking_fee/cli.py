import json
import sys
from collections.abc import Sequence

from parking_fee.calculator import calculate_fee
from parking_fee.parsing import parse_ticket


def main(argv: Sequence[str]) -> int:
    ticket = parse_ticket(argv[0])
    result = calculate_fee(**ticket)
    output = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(output + b"\n")
    return 0
