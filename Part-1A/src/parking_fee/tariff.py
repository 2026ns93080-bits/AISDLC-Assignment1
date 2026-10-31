from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal


VehicleType = Literal["two_wheeler", "car"]


@dataclass(frozen=True, slots=True)
class Tariff:
    grace_minutes: int
    rate_per_started_hour: int
    cap_per_day: int
    lost_ticket_penalty: int


TARIFFS: Final[Mapping[VehicleType, Tariff]] = MappingProxyType(
    {
        "two_wheeler": Tariff(
            grace_minutes=15,
            rate_per_started_hour=20,
            cap_per_day=150,
            lost_ticket_penalty=200,
        ),
        "car": Tariff(
            grace_minutes=15,
            rate_per_started_hour=40,
            cap_per_day=300,
            lost_ticket_penalty=200,
        ),
    }
)
