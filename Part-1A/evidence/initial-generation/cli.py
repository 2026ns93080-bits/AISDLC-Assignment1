import json
import sys
from collections.abc import Sequence

from parking_fee.calculator import calculate_fee
from parking_fee.parsing import ErrorCode, ParkingFeeError, parse_ticket


_ERROR_MESSAGES = {
    ErrorCode.ARGUMENT_COUNT: "error: expected exactly one input file path",
    ErrorCode.CANNOT_READ_FILE: "error: cannot read input file",
    ErrorCode.INVALID_JSON: "error: input must be valid JSON",
    ErrorCode.NOT_JSON_OBJECT: "error: input must be a JSON object",
    ErrorCode.ENTRY_TIMESTAMP: "error: entry must be a timestamp in YYYY-MM-DD HH:MM format",
    ErrorCode.EXIT_TIMESTAMP: "error: exit must be a timestamp in YYYY-MM-DD HH:MM format",
    ErrorCode.VEHICLE_TYPE: "error: vehicle_type must be one of: two_wheeler, car",
    ErrorCode.LOST_TICKET: "error: lost_ticket must be true or false",
    ErrorCode.EXIT_BEFORE_ENTRY: "error: exit must not be earlier than entry",
}


def error_message(code: ErrorCode) -> str:
    return _ERROR_MESSAGES[code]


def main(argv: Sequence[str]) -> int:
    if len(argv) != 1:
        message = error_message(ErrorCode.ARGUMENT_COUNT).encode("utf-8") + b"\n"
        sys.stderr.buffer.write(message)
        return 2

    try:
        ticket = parse_ticket(argv[0])
    except ParkingFeeError as error:
        message = error_message(error.code).encode("utf-8") + b"\n"
        sys.stderr.buffer.write(message)
        return 2

    result = calculate_fee(**ticket)
    output = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(output + b"\n")
    return 0
