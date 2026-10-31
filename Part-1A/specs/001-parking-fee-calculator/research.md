# Research: Parking Fee Calculator

## Decisions

### Module boundaries and runtime

- **Decision**: Implement the CLI, byte/file/JSON parsing, ticket validation, tariff data, and pure fee calculation as separate modules under `src/parking_fee/`. Use Python 3.12+ and the standard library only at runtime.
- **Rationale**: This directly follows the approved module responsibilities and Constitution Principles I–II. The work is a one-file, one-ticket command with no external service or persistence requirement (FR-001–FR-013).
- **Alternatives considered**: A CLI framework or schema-validation package would add runtime dependencies and could change argument/error behavior without providing required value. Neither is used.

### Integer-only tariff calculation

- **Decision**: Store money as whole rupees and time as integer minutes. Derive each timestamp's minute index as `date(y, m, d).toordinal() * 1440 + hour * 60 + minute`; subtract the indices to get duration. For the residual `r` minutes, use integer ceiling division `(r + 59) // 60`.
- **Rationale**: The specified tariff is wholly expressed in integer minutes and rupees. This makes started-hour rounding and each 1440-minute cap block exact and deterministic (FR-006–FR-011; NFR-002).
- **Alternatives considered**: Floating point and `timedelta.total_seconds()` are prohibited by the user constraint and unnecessary. `Decimal` is also unnecessary because the tariff has no fractional currency values.

### Strict file and JSON boundary

- **Decision**: Open the input path in binary mode, require a regular file, reject empty bytes and a leading UTF-8 BOM, decode as strict UTF-8, and call `json.loads` with a duplicate-key-rejecting `object_pairs_hook` and a `parse_constant` hook that rejects `NaN`, `Infinity`, and `-Infinity`. Translate only `UnicodeDecodeError`, `JSONDecodeError`, `ValueError`, and `RecursionError` from this parsing boundary into the JSON error.
- **Rationale**: Binary reads avoid platform-default encodings; strict decoding avoids silently stripping invalid bytes or a BOM. Python's JSON hooks provide the required rejection points without a custom parser. Duplicate keys otherwise risk last-value-wins ambiguity. Deeply nested input must fail as a normal JSON error rather than expose a traceback (FR-002–FR-003, FR-013; NFR-003; AC-025–AC-027, AC-042).
- **Alternatives considered**: `utf-8-sig` would strip and accept the BOM, contrary to AC-042. A custom JSON parser is not warranted. No file-size limit or extra `parse_float` policy is added because neither is specified; unknown properties remain ignored as required by FR-003, and relevant ticket fields are type-checked before use.

### Timestamp profile

- **Decision**: Check exactly 16 characters and an explicit full-match pattern using `[0-9]` for the specified `YYYY-MM-DD HH:MM` form; reject non-ASCII digits. Construct `date(year, month, day)` to validate month/day and explicitly check `0 <= hour <= 23` and `0 <= minute <= 59`.
- **Rationale**: The explicit shape check prevents permissive parser variants, while the calendar constructor validates real dates, including leap days. ASCII-only matching is necessary because Unicode digit predicates accept characters not allowed by the contract (FR-005–FR-006; AC-028–AC-029, AC-038–AC-039, AC-041).
- **Alternatives considered**: `\d`, `str.isdigit()`, and broad ISO/date-time parsing are rejected because they accept forms or digits outside the required profile. `datetime` duration conversion is unnecessary; ordinal minute indices handle date transitions exactly.

### Exact CLI output and errors

- **Decision**: Keep `main(argv)` as the owner of the argument-count check, exact FR-013 message mapping, exit codes, and output. Serialize success with `json.dumps(result, sort_keys=True, separators=(",", ":"))`, encode UTF-8, and write bytes plus one LF to `sys.stdout.buffer`; write errors only to `sys.stderr.buffer`.
- **Rationale**: Binary streams bypass Windows newline translation and encoding defaults. A fixed serializer and error map satisfy byte-for-byte repeatability and prevent incidental output (FR-001, FR-012–FR-013; NFR-001, NFR-003).
- **Alternatives considered**: `print()` and default argument parsers may write translated newlines, usage messages, or diagnostics that violate the byte-exact contract. They are not used.

## Sources

- Python 3.12 standard-library documentation: [`json`](https://docs.python.org/3.12/library/json.html), [`datetime.date`](https://docs.python.org/3.12/library/datetime.html#datetime.date), [`sys` streams](https://docs.python.org/3.12/library/sys.html#sys.stdout), and [binary I/O](https://docs.python.org/3.12/library/io.html#binary-i-o).
- RFC 8259 §8.1, UTF-8 and BOM guidance: https://datatracker.ietf.org/doc/html/rfc8259#section-8.1.
- The approved feature specification and user-provided implementation constraints are authoritative wherever a general best-practice source suggests a different behavior.
