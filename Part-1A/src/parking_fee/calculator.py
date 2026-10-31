from typing import TypedDict

from parking_fee.tariff import TARIFFS, VehicleType


class FeeResult(TypedDict):
    duration_minutes: int
    lost_ticket_penalty: int
    parking_fee: int
    total_fee: int
    vehicle_type: VehicleType


def calculate_fee(
    entry_minute: int,
    exit_minute: int,
    vehicle_type: VehicleType,
    lost_ticket: bool,
) -> FeeResult:
    duration_minutes = exit_minute - entry_minute
    tariff = TARIFFS[vehicle_type]

    if duration_minutes <= tariff.grace_minutes:
        parking_fee = 0
    else:
        started_hours = (duration_minutes + 59) // 60
        parking_fee = started_hours * tariff.rate_per_started_hour

    lost_ticket_penalty = tariff.lost_ticket_penalty if lost_ticket else 0
    return {
        "duration_minutes": duration_minutes,
        "lost_ticket_penalty": lost_ticket_penalty,
        "parking_fee": parking_fee,
        "total_fee": parking_fee + lost_ticket_penalty,
        "vehicle_type": vehicle_type,
    }
