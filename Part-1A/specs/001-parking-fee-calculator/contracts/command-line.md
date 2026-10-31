# Command-Line Contract: Parking Fee Calculator

The command accepts one file path and operates only on that file. Run it as:

```text
python -m parking_fee <path>
```

with `src` on the Python import path (FR-001). An argument beginning with `-` is interpreted as a path, not an option.

## Input

- Exactly one argument is required. Argument-count failure takes precedence over file access.
- The path must refer to a regular file that can be fully opened and read as bytes.
- The bytes must be non-empty strict UTF-8 with no leading UTF-8 BOM and parse as JSON. Duplicate property names at any nesting depth and `NaN`, `Infinity`, or `-Infinity` are rejected.
- The top-level JSON value must be an object. `entry`, `exit`, and `vehicle_type` are required; unknown properties are ignored. `lost_ticket` is optional and defaults to `false`.
- Timestamp strings must be exactly 16 characters in `YYYY-MM-DD HH:MM`, using ASCII `[0-9]` only, valid calendar dates, hours 00–23, and minutes 00–59. Exit must not precede entry.
- `vehicle_type` must be `two_wheeler` or `car`; `lost_ticket`, if present, must be a JSON boolean.

These rules and their order implement FR-001–FR-007 and AC-024–AC-033, AC-040–AC-043. The input data model is described in [data-model.md](../data-model.md).

## Success

- **Exit status**: `0`.
- **Standard output**: exactly one compact JSON object followed by one LF byte (`0A`); standard error is empty.
- **Object fields**: `duration_minutes`, `lost_ticket_penalty`, `parking_fee`, `total_fee`, `vehicle_type`.
- **Serialization**: UTF-8 encoding; alphabetical keys; no spaces (`json.dumps(result, sort_keys=True, separators=(",", ":"))`).
- **Calculation**: whole-minute duration and whole-rupee fees according to the grace period, started-hour rates, 1440-minute caps, and penalty in FR-007–FR-011.

## Failure

- **Exit status**: `2`.
- **Standard output**: empty.
- **Standard error**: exactly one UTF-8 error message followed by one LF byte (`0A`), no traceback or other output.
- **First-failure precedence and exact messages** (FR-013):

| Order | Failure | Message |
|---:|---|---|
| 1 | Argument count is not exactly one | `error: expected exactly one input file path` |
| 2 | File is missing, not regular, or unreadable | `error: cannot read input file` |
| 3 | Input is empty, invalid UTF-8/JSON, BOM-prefixed, has duplicate keys, has a non-finite constant, or exceeds JSON parser recursion | `error: input must be valid JSON` |
| 4 | Top-level JSON value is not an object | `error: input must be a JSON object` |
| 5 | Missing, non-string, malformed, or unreal `entry` | `error: entry must be a timestamp in YYYY-MM-DD HH:MM format` |
| 6 | Missing, non-string, malformed, or unreal `exit` | `error: exit must be a timestamp in YYYY-MM-DD HH:MM format` |
| 7 | Missing, non-string, or unsupported vehicle type | `error: vehicle_type must be one of: two_wheeler, car` |
| 8 | Present `lost_ticket` is not a JSON boolean | `error: lost_ticket must be true or false` |
| 9 | Exit is earlier than entry | `error: exit must not be earlier than entry` |

The CLI checks only the argument count with `len(argv)`, makes no option-parser calls, maps expected failure codes through one message-mapping function, and writes via `sys.stdout.buffer` / `sys.stderr.buffer`. Expected I/O, decode, JSON, validation, and recursion errors are handled at their explicit boundaries; unexpected programming errors are not hidden by a blanket catch (FR-013; NFR-003).
