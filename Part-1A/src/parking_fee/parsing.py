import json
import re
from datetime import date
from typing import TypedDict

from parking_fee.tariff import VehicleType


_TIMESTAMP_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}")


class ParsedTicket(TypedDict):
    entry_minute: int
    exit_minute: int
    vehicle_type: VehicleType
    lost_ticket: bool


def _parse_timestamp(value: object, field: str) -> int:
    if not isinstance(value, str) or len(value) != 16:
        raise ValueError(f"{field} must be a timestamp in YYYY-MM-DD HH:MM format")
    if _TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field} must be a timestamp in YYYY-MM-DD HH:MM format")

    year = int(value[0:4])
    month = int(value[5:7])
    day = int(value[8:10])
    hour = int(value[11:13])
    minute = int(value[14:16])

    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError(f"{field} must be a timestamp in YYYY-MM-DD HH:MM format")

    try:
        timestamp_date = date(year, month, day)
    except ValueError as error:
        raise ValueError(
            f"{field} must be a timestamp in YYYY-MM-DD HH:MM format"
        ) from error

    return timestamp_date.toordinal() * 1440 + hour * 60 + minute


def parse_ticket(path: str) -> ParsedTicket:
    with open(path, "rb") as input_file:
        contents = input_file.read()

    ticket = json.loads(contents.decode("utf-8"))
    if not isinstance(ticket, dict):
        raise ValueError("input must be a JSON object")

    if "entry" not in ticket:
        raise ValueError("entry must be a timestamp in YYYY-MM-DD HH:MM format")
    entry_minute = _parse_timestamp(ticket["entry"], "entry")

    if "exit" not in ticket:
        raise ValueError("exit must be a timestamp in YYYY-MM-DD HH:MM format")
    exit_minute = _parse_timestamp(ticket["exit"], "exit")

    vehicle_type = ticket.get("vehicle_type")
    if vehicle_type == "two_wheeler":
        normalized_vehicle_type: VehicleType = vehicle_type
    elif vehicle_type == "car":
        normalized_vehicle_type = vehicle_type
    else:
        raise ValueError("vehicle_type must be one of: two_wheeler, car")

    lost_ticket = ticket.get("lost_ticket", False)
    if not isinstance(lost_ticket, bool):
        raise ValueError("lost_ticket must be true or false")

    if exit_minute < entry_minute:
        raise ValueError("exit must not be earlier than entry")

    return {
        "entry_minute": entry_minute,
        "exit_minute": exit_minute,
        "vehicle_type": normalized_vehicle_type,
        "lost_ticket": lost_ticket,
    }
