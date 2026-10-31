# Feature Specification: Parking Fee Calculator

**Feature Branch**: `not created by this command`

**Created**: 2026-10-31

**Status**: Approved

**Input**: User description: "Build a Parking Fee Calculator that reads one parking ticket from a JSON file and prints the fee."

## Clarifications

### Session 2026-10-31

- Q: How should a sole command-line argument that starts with "-" (for example --help) be treated: as a file path, or as an option? → A: As a file path.
- Q: Must every digit in a timestamp be an ASCII digit 0 through 9, with other Unicode digits rejected? → A: Yes; timestamp digits must be ASCII 0-9 only.
- Q: What should count as an unreadable input file, including when the supplied path refers to a directory? → A: A path that is not a regular file, or whose contents cannot be fully opened and read as bytes.
- Q: How should a UTF-8 byte-order mark at the very start of the input file be treated? → A: Reject it with the specified JSON error.
- Q: How must duplicate JSON property names be handled? → A: Reject duplicate property names at any nesting depth, including inside properties that are otherwise ignored.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Calculate a parking fee (Priority: P1)

A parking attendant supplies one ticket file and receives the duration, parking fee, any lost-ticket penalty, total fee, and vehicle type in a predictable result.

**Why this priority**: Producing the correct bill for a valid ticket is the feature's primary value.

**Independent Test**: Supply one valid ticket and verify its exit status and exact output line. The example ticket is covered by AC-015.

**Acceptance Scenarios**:

1. **Given** a valid car ticket for 190 minutes, **When** its file path is supplied, **Then** the exact result in AC-015 is printed.
2. **Given** a valid two-wheeler ticket, **When** its file path is supplied, **Then** the fee uses the two-wheeler tariff, as verified by AC-016.

### User Story 2 - Apply grace, tariff, caps, and penalties (Priority: P1)

A parking attendant receives a bill that accounts for the grace period, hourly rounding, full 24-hour blocks, daily caps, and a lost ticket.

**Why this priority**: Correct and consistent application of the published tariff prevents incorrect charges.

**Independent Test**: Supply valid tickets at each specified duration boundary and with or without a lost ticket; compare each complete result line with AC-001 through AC-023 and AC-034 through AC-039.

**Acceptance Scenarios**:

1. **Given** a stay of 15 minutes or less, **When** it is billed, **Then** its parking fee is zero (AC-001 through AC-004).
2. **Given** a stay longer than 15 minutes, **When** it is billed, **Then** each started hour and each 24-hour block is charged according to the tariff (AC-005 through AC-019 and AC-034 through AC-039).
3. **Given** a lost ticket, **When** it is billed, **Then** the penalty is added even if the parking fee is zero (AC-020 and AC-021).

### User Story 3 - Receive a precise error for invalid input (Priority: P1)

A user receives one stable, actionable error message when the argument, file, or ticket is invalid, without a partial result.

**Why this priority**: Clear failure behavior lets users correct an input instead of mistaking an invalid ticket for a valid bill.

**Independent Test**: Supply each invalid argument/file/ticket vector and verify the exit status, empty standard output, exact error line, and precedence in AC-024 through AC-033 and AC-040 through AC-042.

**Acceptance Scenarios**:

1. **Given** an invalid argument count, **When** the command is invoked, **Then** the argument-count error wins over file errors (AC-024 and AC-033).
2. **Given** a ticket with multiple invalid fields, **When** it is read, **Then** the first failing validation in the specified order determines the sole error (AC-033).

### Edge Cases

- Valid zero-duration, grace-period, hourly-rounding, and single- and multi-day tariff cases cover both vehicle types, including lost-ticket handling (AC-001 through AC-023).
- Additional valid cases cover hourly-cap boundaries, a year transition, and a leap-year transition (AC-034 through AC-039).
- Invalid argument counts produce the argument-count error (AC-024); missing input paths and directory paths produce the file-read error (AC-025); a sole `--help` argument is treated as a missing input-file path (AC-040).
- Empty, wrongly encoded, malformed, duplicate-key (including nested duplicates inside otherwise ignored properties), or byte-order-mark-prefixed JSON produces the JSON error; valid JSON with a non-object top-level value produces the object error (AC-026, AC-027, AC-042, and AC-043).
- Invalid entry and exit timestamps, including an entry timestamp with fullwidth digits, produce their respective timestamp errors (AC-028, AC-029, and AC-041).
- Invalid vehicle types, invalid lost-ticket values, earlier exit times, and validation-precedence conflicts produce the defined errors (AC-030 through AC-033).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The command MUST accept exactly one command-line argument, interpreted as the input file path, even when it starts with `-` (for example, `--help`).
- **FR-002**: The command MUST report a missing path, a path that does not refer to a regular file (including a directory), or a file whose contents cannot be fully opened and read as bytes using the specified file-read error.
- **FR-003**: The input file MUST contain valid UTF-8 JSON whose top-level value is an object. An empty file, invalid UTF-8, a UTF-8 byte-order mark at the start, invalid JSON, or duplicate property names at any nesting depth, including inside properties that are otherwise ignored, MUST use the specified JSON error. Properties other than `entry`, `exit`, `vehicle_type`, and `lost_ticket` MUST be ignored except that their contents MUST still be checked for duplicate property names.
- **FR-004**: The object MUST contain string values for `entry`, `exit`, and `vehicle_type`. `lost_ticket` MAY be omitted; when present it MUST be a JSON boolean, and omission MUST mean false.
- **FR-005**: Each timestamp MUST be exactly 16 characters in the form `YYYY-MM-DD HH:MM`, with zero-padded fields using ASCII digits `0` through `9` only, no seconds or time zone, and a real calendar date and time.
- **FR-006**: The exit timestamp MUST be equal to or later than the entry timestamp. Duration MUST be the whole number of minutes between the two timestamps; equal timestamps yield zero.
- **FR-007**: The default tariff data used by the calculation MUST use the following values:

  | Tariff item | two_wheeler | car |
  |---|---:|---:|
  | Rate per started hour | 20 rupees | 40 rupees |
  | Cap per 24-hour block | 150 rupees | 300 rupees |

  The grace period is 15 minutes for either vehicle type. The lost-ticket penalty is 200 rupees for either vehicle type.
- **FR-008**: For a duration of 15 minutes or less, the parking fee MUST be zero. The lost-ticket penalty, if any, MUST still apply.
- **FR-009**: For a duration longer than 15 minutes, the full stay duration MUST be billed; the grace period MUST NOT be deducted. Each started hour MUST be charged at the vehicle's hourly rate.
- **FR-010**: For a duration `D` greater than 15 minutes, the parking fee MUST equal `(D // 1440) * cap + min(cap, ceil((D % 1440) / 60) * rate)`. Each complete 1440-minute block receives one cap, and the remaining minutes are billed in started hours up to one cap.
- **FR-011**: The total fee MUST equal the parking fee plus the lost-ticket penalty.
- **FR-012**: On success, the command MUST exit with status 0 and write exactly one line to standard output: a compact JSON object followed by one newline. The object MUST contain exactly five keys, duration_minutes, lost_ticket_penalty, parking_fee, total_fee and vehicle_type, in that alphabetical order, with no spaces and no other keys. duration_minutes, lost_ticket_penalty, parking_fee and total_fee MUST be JSON integers written without a decimal point or exponent; vehicle_type MUST be a JSON string. Standard error MUST be empty.
- **FR-013**: On failure, the command MUST exit with status 2, write nothing to standard output, and write exactly one line to standard error: the applicable message below followed by one newline. The first failing check MUST win, in this order:
  1. Argument count — `error: expected exactly one input file path`
  2. File missing or unreadable — `error: cannot read input file`
  3. Empty file, invalid UTF-8, or invalid JSON — `error: input must be valid JSON`
  4. Top-level JSON value is not an object — `error: input must be a JSON object`
  5. Missing, non-string, malformed, or unreal `entry` — `error: entry must be a timestamp in YYYY-MM-DD HH:MM format`
  6. Missing, non-string, malformed, or unreal `exit` — `error: exit must be a timestamp in YYYY-MM-DD HH:MM format`
  7. Missing, non-string, or unsupported `vehicle_type` — `error: vehicle_type must be one of: two_wheeler, car`
  8. Present `lost_ticket` is not a JSON boolean, including null — `error: lost_ticket must be true or false`
  9. Exit is earlier than entry — `error: exit must not be earlier than entry`

### Non-Functional Requirements

- **NFR-001**: Repeating a calculation with identical input MUST produce byte-identical standard output or standard error and the same exit status.
- **NFR-002**: Durations and all fee amounts MUST be whole numbers; fee amounts MUST be expressed in rupees.
- **NFR-003**: Failure handling MUST not emit partial results or a stack trace; it MUST follow the single-line error contract in FR-013.

### Acceptance Criteria

For all success cases below, invoke the command with exactly the argument `ticket.json`; the file contains exactly the listed UTF-8 JSON text with no trailing bytes. The expected standard output is the listed JSON text followed by one LF (`\n`); the exit status is `0` and standard error is empty.

| ID | Verifies | Exact input file content | Exact expected standard output |
|---|---|---|---|
| **AC-001** | FR-006, FR-008, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 10:00","vehicle_type":"car"}` | `{"duration_minutes":0,"lost_ticket_penalty":0,"parking_fee":0,"total_fee":0,"vehicle_type":"car"}` |
| **AC-002** | FR-006, FR-008, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 10:00","vehicle_type":"two_wheeler"}` | `{"duration_minutes":0,"lost_ticket_penalty":0,"parking_fee":0,"total_fee":0,"vehicle_type":"two_wheeler"}` |
| **AC-003** | FR-008, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 10:15","vehicle_type":"car"}` | `{"duration_minutes":15,"lost_ticket_penalty":0,"parking_fee":0,"total_fee":0,"vehicle_type":"car"}` |
| **AC-004** | FR-008, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 10:15","vehicle_type":"two_wheeler"}` | `{"duration_minutes":15,"lost_ticket_penalty":0,"parking_fee":0,"total_fee":0,"vehicle_type":"two_wheeler"}` |
| **AC-005** | FR-007, FR-009, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 10:16","vehicle_type":"car"}` | `{"duration_minutes":16,"lost_ticket_penalty":0,"parking_fee":40,"total_fee":40,"vehicle_type":"car"}` |
| **AC-006** | FR-007, FR-009, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 10:16","vehicle_type":"two_wheeler"}` | `{"duration_minutes":16,"lost_ticket_penalty":0,"parking_fee":20,"total_fee":20,"vehicle_type":"two_wheeler"}` |
| **AC-007** | FR-007, FR-009, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00","vehicle_type":"car"}` | `{"duration_minutes":60,"lost_ticket_penalty":0,"parking_fee":40,"total_fee":40,"vehicle_type":"car"}` |
| **AC-008** | FR-007, FR-009, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00","vehicle_type":"two_wheeler"}` | `{"duration_minutes":60,"lost_ticket_penalty":0,"parking_fee":20,"total_fee":20,"vehicle_type":"two_wheeler"}` |
| **AC-009** | FR-007, FR-009, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:01","vehicle_type":"car"}` | `{"duration_minutes":61,"lost_ticket_penalty":0,"parking_fee":80,"total_fee":80,"vehicle_type":"car"}` |
| **AC-010** | FR-007, FR-009, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:01","vehicle_type":"two_wheeler"}` | `{"duration_minutes":61,"lost_ticket_penalty":0,"parking_fee":40,"total_fee":40,"vehicle_type":"two_wheeler"}` |
| **AC-011** | FR-007, FR-010, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-02 10:00","vehicle_type":"car"}` | `{"duration_minutes":1440,"lost_ticket_penalty":0,"parking_fee":300,"total_fee":300,"vehicle_type":"car"}` |
| **AC-012** | FR-007, FR-010, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-02 10:00","vehicle_type":"two_wheeler"}` | `{"duration_minutes":1440,"lost_ticket_penalty":0,"parking_fee":150,"total_fee":150,"vehicle_type":"two_wheeler"}` |
| **AC-013** | FR-007, FR-010, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-02 10:01","vehicle_type":"car"}` | `{"duration_minutes":1441,"lost_ticket_penalty":0,"parking_fee":340,"total_fee":340,"vehicle_type":"car"}` |
| **AC-014** | FR-007, FR-010, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-02 10:01","vehicle_type":"two_wheeler"}` | `{"duration_minutes":1441,"lost_ticket_penalty":0,"parking_fee":170,"total_fee":170,"vehicle_type":"two_wheeler"}` |
| **AC-015** | FR-007, FR-009, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 13:10","vehicle_type":"car"}` | `{"duration_minutes":190,"lost_ticket_penalty":0,"parking_fee":160,"total_fee":160,"vehicle_type":"car"}` |
| **AC-016** | FR-007, FR-009, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 13:10","vehicle_type":"two_wheeler"}` | `{"duration_minutes":190,"lost_ticket_penalty":0,"parking_fee":80,"total_fee":80,"vehicle_type":"two_wheeler"}` |
| **AC-017** | FR-009, FR-010, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-02 10:15","vehicle_type":"car"}` | `{"duration_minutes":1455,"lost_ticket_penalty":0,"parking_fee":340,"total_fee":340,"vehicle_type":"car"}` |
| **AC-018** | FR-007, FR-010, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-02 19:20","vehicle_type":"car"}` | `{"duration_minutes":2000,"lost_ticket_penalty":0,"parking_fee":600,"total_fee":600,"vehicle_type":"car"}` |
| **AC-019** | FR-007, FR-010, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-02 19:20","vehicle_type":"two_wheeler"}` | `{"duration_minutes":2000,"lost_ticket_penalty":0,"parking_fee":300,"total_fee":300,"vehicle_type":"two_wheeler"}` |
| **AC-020** | FR-008, FR-011, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 10:00","vehicle_type":"car","lost_ticket":true}` | `{"duration_minutes":0,"lost_ticket_penalty":200,"parking_fee":0,"total_fee":200,"vehicle_type":"car"}` |
| **AC-021** | FR-011, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:01","vehicle_type":"two_wheeler","lost_ticket":true}` | `{"duration_minutes":61,"lost_ticket_penalty":200,"parking_fee":40,"total_fee":240,"vehicle_type":"two_wheeler"}` |
| **AC-022** | FR-004, FR-011, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 10:16","vehicle_type":"car","lost_ticket":false}` | `{"duration_minutes":16,"lost_ticket_penalty":0,"parking_fee":40,"total_fee":40,"vehicle_type":"car"}` |
| **AC-023** | FR-003, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 10:16","vehicle_type":"car","reference":"ignored"}` | `{"duration_minutes":16,"lost_ticket_penalty":0,"parking_fee":40,"total_fee":40,"vehicle_type":"car"}` |

For every error case below, the exact expected exit status is `2`, standard output is empty, and standard error is the quoted message followed by one LF (`\n`).

| ID | Verifies | Exact invocation and input | Exact expected standard error |
|---|---|---|---|
| **AC-024** | FR-001, FR-013 | Invoke once with no arguments, and once with exactly `missing-a.json` and `missing-b.json` as two arguments. No file needs to exist. | `error: expected exactly one input file path` |
| **AC-025** | FR-002, FR-013 | Test (a) argument `missing.json`, whose path does not exist; (b) argument `directory`, whose path exists and refers to a directory. | `error: cannot read input file` |
| **AC-026** | FR-003, FR-013 | Argument: `ticket.json`; test each exact file content: (a) zero bytes, (b) the single byte `0xFF`, (c) the two-byte text `{` followed by `[` (`{[`), (d) `{"entry":"2026-01-01 10:00","entry":"2026-01-01 11:00","exit":"2026-01-01 12:00","vehicle_type":"car"}`. | `error: input must be valid JSON` |
| **AC-027** | FR-003, FR-013 | Argument: `ticket.json`; test each valid JSON content that is not an object: `[]`, `null`, and `"ticket"`. | `error: input must be a JSON object` |
| **AC-028** | FR-004, FR-005, FR-013 | Argument: `ticket.json`; test each content: (a) `{"exit":"2026-01-01 11:00","vehicle_type":"car"}`; (b) `{"entry":1,"exit":"2026-01-01 11:00","vehicle_type":"car"}`; (c) `{"entry":"2026-1-01 10:00","exit":"2026-01-01 11:00","vehicle_type":"car"}`; (d) `{"entry":"2026-02-29 10:00","exit":"2026-03-01 10:00","vehicle_type":"car"}`; (e) `{"entry":"2026-01-01 24:00","exit":"2026-01-02 10:00","vehicle_type":"car"}`. | `error: entry must be a timestamp in YYYY-MM-DD HH:MM format` |
| **AC-029** | FR-004, FR-005, FR-013 | Argument: `ticket.json`; test each content: (a) `{"entry":"2026-01-01 10:00","vehicle_type":"car"}`; (b) `{"entry":"2026-01-01 10:00","exit":null,"vehicle_type":"car"}`; (c) `{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00:00","vehicle_type":"car"}`; (d) `{"entry":"2026-04-30 10:00","exit":"2026-04-31 10:00","vehicle_type":"car"}`. | `error: exit must be a timestamp in YYYY-MM-DD HH:MM format` |
| **AC-030** | FR-004, FR-007, FR-013 | Argument: `ticket.json`; test each content: (a) `{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00"}`; (b) `{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00","vehicle_type":1}`; (c) `{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00","vehicle_type":"Car"}`. | `error: vehicle_type must be one of: two_wheeler, car` |
| **AC-031** | FR-004, FR-013 | Argument: `ticket.json`; test each content: (a) `{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00","vehicle_type":"car","lost_ticket":null}`; (b) `{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00","vehicle_type":"car","lost_ticket":"true"}`. | `error: lost_ticket must be true or false` |
| **AC-032** | FR-006, FR-013 | Argument: `ticket.json`; content: `{"entry":"2026-01-01 11:00","exit":"2026-01-01 10:59","vehicle_type":"car","lost_ticket":false}`. | `error: exit must not be earlier than entry` |
| **AC-033** | FR-001 through FR-006, FR-013 | Run the following precedence vectors independently. (a) Two arguments `missing-a.json`, `missing-b.json` → `error: expected exactly one input file path`. (b) One argument `missing.json`, path absent → `error: cannot read input file`. (c) `ticket.json` contains `{[` → `error: input must be valid JSON`. (d) `ticket.json` contains `[]` → `error: input must be a JSON object`. (e) `ticket.json` contains `{"entry":"bad","exit":"bad","vehicle_type":"unknown","lost_ticket":null}` → `error: entry must be a timestamp in YYYY-MM-DD HH:MM format`. (f) `ticket.json` contains `{"entry":"2026-01-01 10:00","exit":"bad","vehicle_type":"unknown","lost_ticket":null}` → `error: exit must be a timestamp in YYYY-MM-DD HH:MM format`. (g) `ticket.json` contains `{"entry":"2026-01-01 11:00","exit":"2026-01-01 10:59","vehicle_type":"unknown","lost_ticket":null}` → `error: vehicle_type must be one of: two_wheeler, car`. (h) `ticket.json` contains `{"entry":"2026-01-01 11:00","exit":"2026-01-01 10:59","vehicle_type":"car","lost_ticket":null}` → `error: lost_ticket must be true or false`. (i) `ticket.json` contains `{"entry":"2026-01-01 11:00","exit":"2026-01-01 10:59","vehicle_type":"car","lost_ticket":false}` → `error: exit must not be earlier than entry`. | For each vector, standard error MUST equal the exact quoted message for that vector followed by one LF (`\n`); standard output is empty and exit status is `2`. |
| **AC-040** | FR-001, FR-002, FR-013 | Invoke with exactly one argument, `--help`, and ensure no file with that name exists at the path resolved by the command. | `error: cannot read input file` |
| **AC-041** | FR-005, FR-013 | Argument: `ticket.json`; content: `{"entry":"２０２６-０１-０１ １０:００","exit":"2026-01-01 11:00","vehicle_type":"car"}`. | `error: entry must be a timestamp in YYYY-MM-DD HH:MM format` |
| **AC-042** | FR-003, FR-013 | Argument: `ticket.json`; file bytes: a UTF-8 byte-order mark (`EF BB BF`) followed immediately by the valid JSON text `{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00","vehicle_type":"car"}`. | `error: input must be valid JSON` |
| **AC-043** | FR-003, FR-013 | Argument: `ticket.json`; file content: `{"entry":"2026-01-01 10:00","exit":"2026-01-01 11:00","vehicle_type":"car","extra":{"a":1,"a":2}}`. | `error: input must be valid JSON` |

For the following additional success cases, invoke the command with exactly the argument `ticket.json`; the file contains exactly the listed UTF-8 JSON text with no trailing bytes. The expected standard output is the listed JSON text followed by one LF (`\n`); the exit status is `0` and standard error is empty.

| ID | Verifies | Exact input file content | Exact expected standard output |
|---|---|---|---|
| **AC-034** | FR-007, FR-010, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 17:00","vehicle_type":"car"}` | `{"duration_minutes":420,"lost_ticket_penalty":0,"parking_fee":280,"total_fee":280,"vehicle_type":"car"}` |
| **AC-035** | FR-007, FR-010, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 17:01","vehicle_type":"car"}` | `{"duration_minutes":421,"lost_ticket_penalty":0,"parking_fee":300,"total_fee":300,"vehicle_type":"car"}` |
| **AC-036** | FR-007, FR-010, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 17:00","vehicle_type":"two_wheeler"}` | `{"duration_minutes":420,"lost_ticket_penalty":0,"parking_fee":140,"total_fee":140,"vehicle_type":"two_wheeler"}` |
| **AC-037** | FR-007, FR-010, FR-012 | `{"entry":"2026-01-01 10:00","exit":"2026-01-01 17:01","vehicle_type":"two_wheeler"}` | `{"duration_minutes":421,"lost_ticket_penalty":0,"parking_fee":150,"total_fee":150,"vehicle_type":"two_wheeler"}` |
| **AC-038** | FR-006, FR-007, FR-009, FR-012 | `{"entry":"2026-12-31 23:50","exit":"2027-01-01 00:10","vehicle_type":"car"}` | `{"duration_minutes":20,"lost_ticket_penalty":0,"parking_fee":40,"total_fee":40,"vehicle_type":"car"}` |
| **AC-039** | FR-006, FR-007, FR-010, FR-012 | `{"entry":"2028-02-28 12:00","exit":"2028-03-01 12:00","vehicle_type":"car"}` | `{"duration_minutes":2880,"lost_ticket_penalty":0,"parking_fee":600,"total_fee":600,"vehicle_type":"car"}` |

### Key Entities *(include if feature involves data)*

- **Parking ticket**: One input record containing entry and exit timestamps, a vehicle type, and an optional lost-ticket flag; unrelated properties are ignored.
- **Tariff**: The default grace period, per-vehicle hourly rate and 24-hour cap, and lost-ticket penalty used to calculate charges.
- **Fee result**: The duration, parking fee, lost-ticket penalty, total fee, and vehicle type returned for a valid ticket.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every valid-input acceptance criterion (AC-001 through AC-023 and AC-034 through AC-039) produces the exact specified exit status and output line, with no additional standard output or standard error.
- **SC-002**: All invalid-input cases AC-024 through AC-033 and AC-040 through AC-043 produce exit status 2, empty standard output, and only the exact specified error line on standard error.
- **SC-003**: Repeating any acceptance case with identical arguments, file bytes, and file availability produces identical output bytes and exit status.

## Assumptions

- A command-line argument is the single file path to one ticket; the ticket is not supplied through standard input.
- The default tariff values in FR-007 apply unless a later specification explicitly changes them.
- An error line ends in one newline; the successful output line ends in one newline.
- Performance, throughput, and observability targets are intentionally not specified because they are out of scope.

## Out of Scope

Multiple tickets per file, time zones and daylight saving, seconds, payments, persistence, databases, networking, user interfaces, additional vehicle types, holiday or night rates, and performance or observability targets are excluded.
