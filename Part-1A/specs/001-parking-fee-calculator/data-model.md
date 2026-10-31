# Data Model: Parking Fee Calculator

This design translates the input record into validated integer-minute indices and a fee result. Parsing and calculations use no floating-point values; rupee amounts and durations are integers (FR-005–FR-011; NFR-002).

## Input Parking Ticket

One JSON object represents one ticket (FR-001, FR-003–FR-004).

| Property | Input type | Validation / meaning |
|---|---|---|
| `entry` | string, required | Exactly 16 characters, `YYYY-MM-DD HH:MM`, ASCII digits only, real date and time (FR-005). |
| `exit` | string, required | Same timestamp rules as `entry` (FR-005). Must not precede `entry` (FR-006). |
| `vehicle_type` | string, required | Exactly `two_wheeler` or `car` (FR-004, FR-007). |
| `lost_ticket` | boolean, optional | Defaults to `false` when absent; any present non-boolean value, including `null`, is invalid (FR-004). |
| other properties | any valid JSON value | Ignored (FR-003). |

The JSON input must be non-empty, strict UTF-8, and have no leading UTF-8 BOM. Its top-level value must be an object. Duplicate property names at any nesting depth and non-standard constants (`NaN`, `Infinity`, `-Infinity`) are rejected (FR-003; AC-043).

## Validated Ticket

`parsing.py` returns a validated ticket for calculation. This normalized record has:

| Field | Type | Meaning |
|---|---|---|
| `entry_minute` | integer | `date(y, m, d).toordinal() * 1440 + hour * 60 + minute` for the entry timestamp. |
| `exit_minute` | integer | Same minute-index calculation for exit. |
| `vehicle_type` | literal string | One of the two supported tariff keys. |
| `lost_ticket` | boolean | Validated input value or `false` when omitted. |

The index is based on a fixed ordinal-minute epoch; duration is `exit_minute - entry_minute`, a plain integer difference. Timestamp shape is checked with an explicit `[0-9]` pattern and exact length before calendar validation with `date(y, m, d)`; hour and minute bounds are checked explicitly. No `timedelta.total_seconds()`, floating point, `\d`, or `str.isdigit()` is used (FR-005–FR-006; AC-028–AC-029, AC-038–AC-039, AC-041).

## Tariff

`tariff.py` contains data only: one immutable mapping keyed by `vehicle_type`, with frozen tariff values. Each value carries the same grace period and lost-ticket penalty plus that vehicle's rate and 1440-minute-block cap (FR-007).

| Key | Grace minutes | Rate per started hour (rupees) | Cap per 1440-minute block (rupees) | Lost-ticket penalty (rupees) |
|---|---:|---:|---:|---:|
| `two_wheeler` | 15 | 20 | 150 | 200 |
| `car` | 15 | 40 | 300 | 200 |

## Fee Result

The calculator returns a result containing exactly the values serialized by the CLI (FR-011–FR-012):

| Field | Type | Meaning |
|---|---|---|
| `duration_minutes` | integer | Whole-minute stay duration. |
| `lost_ticket_penalty` | integer | 200 rupees when `lost_ticket` is true, otherwise 0. |
| `parking_fee` | integer | Fee from the grace, started-hour, and per-block cap rules. |
| `total_fee` | integer | `parking_fee + lost_ticket_penalty`. |
| `vehicle_type` | string | Validated input type. |

The output object is serialized with sorted keys, compact separators, UTF-8, and one trailing LF (FR-012; NFR-001).

## Validation and Calculation Rules

Validation errors are decided in this order (FR-013):

1. Argument count.
2. Missing, non-regular, or unreadable file.
3. Empty input, invalid UTF-8, BOM, duplicate property names at any nesting depth, malformed JSON, non-standard constant, or excessive nesting raising `RecursionError`.
4. Top-level JSON object.
5. `entry` presence, type, shape, and real timestamp.
6. `exit` presence, type, shape, and real timestamp.
7. Supported `vehicle_type`.
8. `lost_ticket` type when present.
9. Exit not earlier than entry.

For duration `D <= 15`, `parking_fee = 0`. Otherwise, with `q = D // 1440`, `r = D % 1440`, and `remaining_hours = (r + 59) // 60`, `parking_fee = q * cap + min(cap, remaining_hours * rate)`. This bills the full stay after grace, charges each started residual hour, and applies one cap per complete 1440-minute block (FR-008–FR-010). The lost-ticket penalty is added even when the parking fee is zero (FR-008, FR-011).

## Error Model

Parsing and CLI failures use explicit expected error codes. A single `error_message` function maps them to the exact FR-013 messages; validation order above determines which code wins. The CLI writes no stdout bytes on failure and emits the mapped message followed by exactly one LF to stderr, returning 2. Success returns 0 (FR-012–FR-013; NFR-003).
