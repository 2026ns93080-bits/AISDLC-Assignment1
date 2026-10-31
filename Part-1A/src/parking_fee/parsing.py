import json
import os
import re
import stat
from datetime import date
from enum import StrEnum
from typing import TypedDict

from parking_fee.tariff import VehicleType


_TIMESTAMP_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}")


class ErrorCode(StrEnum):
    ARGUMENT_COUNT = "argument_count"
    CANNOT_READ_FILE = "cannot_read_file"
    INVALID_JSON = "invalid_json"
    NOT_JSON_OBJECT = "not_json_object"
    ENTRY_TIMESTAMP = "entry_timestamp"
    EXIT_TIMESTAMP = "exit_timestamp"
    VEHICLE_TYPE = "vehicle_type"
    LOST_TICKET = "lost_ticket"
    EXIT_BEFORE_ENTRY = "exit_before_entry"


class ParkingFeeError(ValueError):
    def __init__(self, code: ErrorCode) -> None:
        self.code = code
        super().__init__(code.value)


class _InvalidJSONValue(ValueError):
    pass


class ParsedTicket(TypedDict):
    entry_minute: int
    exit_minute: int
    vehicle_type: VehicleType
    lost_ticket: bool


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _InvalidJSONValue
        result[key] = value
    return result


def _reject_non_finite_constant(value: str) -> None:
    raise _InvalidJSONValue(value)


def _parse_timestamp(value: object, field: str) -> int:
    code = (
        ErrorCode.ENTRY_TIMESTAMP
        if field == "entry"
        else ErrorCode.EXIT_TIMESTAMP
    )
    if not isinstance(value, str) or len(value) != 16:
        raise ParkingFeeError(code)
    if _TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ParkingFeeError(code)

    year = int(value[0:4])
    month = int(value[5:7])
    day = int(value[8:10])
    hour = int(value[11:13])
    minute = int(value[14:16])

    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ParkingFeeError(code)

    try:
        timestamp_date = date(year, month, day)
    except ValueError as error:
        raise ParkingFeeError(code) from error

    return timestamp_date.toordinal() * 1440 + hour * 60 + minute


def parse_ticket(path: str) -> ParsedTicket:
    try:
        file_mode = os.stat(path).st_mode
    except (OSError, ValueError) as error:
        raise ParkingFeeError(ErrorCode.CANNOT_READ_FILE) from error
    if not stat.S_ISREG(file_mode):
        raise ParkingFeeError(ErrorCode.CANNOT_READ_FILE)

    try:
        with open(path, "rb") as input_file:
            contents = input_file.read()
    except (OSError, ValueError) as error:
        raise ParkingFeeError(ErrorCode.CANNOT_READ_FILE) from error

    if not contents or contents.startswith(b"\xef\xbb\xbf"):
        raise ParkingFeeError(ErrorCode.INVALID_JSON)
    try:
        decoded_contents = contents.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ParkingFeeError(ErrorCode.INVALID_JSON) from error

    try:
        ticket = json.loads(
            decoded_contents,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite_constant,
        )
    except (ValueError, RecursionError) as error:
        raise ParkingFeeError(ErrorCode.INVALID_JSON) from error

    if not isinstance(ticket, dict):
        raise ParkingFeeError(ErrorCode.NOT_JSON_OBJECT)

    if "entry" not in ticket:
        raise ParkingFeeError(ErrorCode.ENTRY_TIMESTAMP)
    entry_minute = _parse_timestamp(ticket["entry"], "entry")

    if "exit" not in ticket:
        raise ParkingFeeError(ErrorCode.EXIT_TIMESTAMP)
    exit_minute = _parse_timestamp(ticket["exit"], "exit")

    vehicle_type = ticket.get("vehicle_type")
    if vehicle_type == "two_wheeler":
        normalized_vehicle_type: VehicleType = vehicle_type
    elif vehicle_type == "car":
        normalized_vehicle_type = vehicle_type
    else:
        raise ParkingFeeError(ErrorCode.VEHICLE_TYPE)

    lost_ticket = ticket.get("lost_ticket", False)
    if not isinstance(lost_ticket, bool):
        raise ParkingFeeError(ErrorCode.LOST_TICKET)

    if exit_minute < entry_minute:
        raise ParkingFeeError(ErrorCode.EXIT_BEFORE_ENTRY)

    return {
        "entry_minute": entry_minute,
        "exit_minute": exit_minute,
        "vehicle_type": normalized_vehicle_type,
        "lost_ticket": lost_ticket,
    }
