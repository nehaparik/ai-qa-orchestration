# Week 1 API Case Matrix

This matrix catalogs every **unique** API scenario exercised across the
Week 1 test suite (Day 1 + Day 2), after removing repeated teaching
demonstrations, fault-injected reruns, and non-API validator examples.
It exists so the actual breadth of coverage can be judged directly,
separately from the raw pytest test count (see "Counting notes" below).

All scenarios use the real, running FastAPI app
(`app/main.py`), the real synthetic data files (`data/employees.json`,
`data/tickets.json`, `data/service_status.json`), and the real demo
header mechanism (`X-Demo-Employee-ID`). No endpoint, field, or employee
not already present in the actual project was invented to pad this list.

## Columns

- **Case ID** — this matrix's own identifier (`WK1-NN`), independent of
  any pytest test name.
- **Requirement/Contract** — the business rule (BR01–BR04, from
  `docs/business_rules.md`), a JSON Schema file, or "observed behavior"
  when no written rule covers it.
- **Scenario** — what the case actually does.
- **Employee context** — which synthetic employee(s)/ticket(s) are used.
- **Expected result** — the status code and the key thing checked about
  the body.
- **Category** — `positive`, `negative`, `ownership-positive`,
  `ownership-negative`, or `schema`.
- **Executable test** — the file/test (or parametrize id) that actually
  runs this scenario today. Where more than one test exercises the exact
  same request+check, only the first is the canonical executable test;
  the rest are listed as "(overlap)" and are not counted again.

## Matrix

| Case ID | Requirement/Contract | Scenario | Employee context | Expected result | Category | Executable test |
| --- | --- | --- | --- | --- | --- | --- |
| WK1-01 | BR01 | Known employee retrieves own profile | EMP001 (Dana Whitfield) | 200; `employee_id`/`full_name` correct | positive | `tests/test_employees.py::test_get_my_profile_returns_known_employee` |
| WK1-02 | BR02 | Employee retrieves own ticket | EMP001 owns TCK-1001 | 200; `ticket_id` correct | ownership-positive | `tests/test_tickets.py::test_get_own_ticket_returns_200` (overlap: `tests/day2/test_01_fixtures.py::test_employee_a_retrieves_own_ticket`, `tests/day2/test_02_parameterized.py::test_ticket_access_matrix[employee_a_own_ticket__overlaps_test_01_fixtures]`) |
| WK1-03 | BR02 | Employee denied another employee's ticket | EMP002 requests EMP001's TCK-1001 | 403 | ownership-negative | `tests/test_tickets.py::test_get_other_employees_ticket_returns_403` (overlap: `tests/day2/test_02_parameterized.py::test_ticket_access_matrix[employee_b_requests_employee_a_ticket_denied]`, `tests/day2/test_03_ownership.py::test_employee_b_cannot_view_employee_as_ticket`) |
| WK1-04 | Schema: `schemas/ticket.schema.json` | Ticket response conforms to the documented ticket schema | EMP001 / TCK-1001 | 200; full schema valid | schema | `tests/test_tickets.py::test_ticket_matches_schema` (overlap: `tests/day2/test_04_schema.py::test_ticket_matches_schema`) |
| WK1-05 | Basic health contract | Health check succeeds with no auth | none | 200; `status == "ok"` | positive | `tests/test_service_status.py::test_health_check_returns_ok` |
| WK1-06 | BR04 | VPN status has a defined status and update time | none | 200; `status` in enum, `updated_at` present | positive | `tests/test_service_status.py::test_vpn_status_has_defined_status_and_update_time` |
| WK1-07 | BR02 | Second employee retrieves own ticket | EMP002 owns TCK-1002 | 200; `ticket_id` correct | ownership-positive | `tests/day2/test_01_fixtures.py::test_employee_b_retrieves_own_ticket` (overlap: `tests/day2/test_02_parameterized.py::test_ticket_access_matrix[employee_b_own_ticket__overlaps_test_01_fixtures]`) |
| WK1-08 | BR02 | Cross-ownership denial, opposite direction | EMP001 requests EMP002's TCK-1002 | 403; documented denial message; no leaked ticket content | ownership-negative | `tests/day2/test_03_ownership.py::test_employee_a_cannot_view_employee_bs_ticket` (overlap: `tests/day2/test_02_parameterized.py::test_ticket_access_matrix[employee_a_requests_employee_b_ticket_denied]`) |
| WK1-09 | BR03 | Well-formed but nonexistent ticket id | EMP001 requests TCK-9999 | 404 | negative | `tests/day2/test_02_parameterized.py::test_ticket_access_matrix[valid_employee_requests_missing_wellformed_ticket]` |
| WK1-10 | Schema: `schemas/employee_profile.schema.json` | Employee profile conforms to the documented schema | EMP001 | 200; full schema valid | schema | `tests/day2/test_04_schema.py::test_employee_profile_matches_schema` |
| WK1-11 | Schema: `schemas/service_status.schema.json` | VPN status conforms to the documented schema | none | 200; full schema valid | schema | `tests/day2/test_04_schema.py::test_service_status_matches_schema` |
| WK1-12 | Schema: `schemas/error_response.schema.json` | 404 error body conforms to the documented error schema | EMP001 / TCK-9999 | 404; full schema valid | schema | `tests/day2/test_04_schema.py::test_missing_ticket_error_matches_schema` |
| WK1-13 | BR01 | Missing demo header on profile endpoint | none | 400; `"Missing required header..."` | negative | `tests/day2/test_05_week1_coverage.py::test_missing_header_on_profile_returns_400` |
| WK1-14 | BR01 | Unknown employee id on profile endpoint | EMP999 (does not exist) | 400; `"Unknown demo employee id..."` | negative | `tests/day2/test_05_week1_coverage.py::test_unknown_employee_id_on_profile_returns_400` |
| WK1-15 | BR01 | Missing demo header on the ticket endpoint (same shared auth dependency) | none / TCK-1001 | 400, before the ownership check ever runs | negative | `tests/day2/test_05_week1_coverage.py::test_missing_header_on_ticket_endpoint_returns_400` |
| WK1-16 | BR01 | Third known employee retrieves own profile | EMP003 (Priya Nair) | 200; correct fields | positive | `tests/day2/test_05_week1_coverage.py::test_employee_c_retrieves_own_profile` |
| WK1-17 | BR02 | Third employee retrieves own ticket | EMP003 owns TCK-1003 | 200 | ownership-positive | `tests/day2/test_05_week1_coverage.py::test_employee_c_retrieves_own_ticket` |
| WK1-18 | BR02 | Fourth employee retrieves own ticket | EMP004 owns TCK-1004 | 200 | ownership-positive | `tests/day2/test_05_week1_coverage.py::test_employee_d_retrieves_own_ticket` |
| WK1-19 | BR02 | Cross-ownership denial, a new employee pair (not EMP001/EMP002) | EMP003 requests EMP004's TCK-1004 | 403; no leaked ticket content | ownership-negative | `tests/day2/test_05_week1_coverage.py::test_employee_c_cannot_view_employee_ds_ticket` |
| WK1-20 | BR02 | An owner's *second* ticket is still correctly recognized as theirs | EMP001 also owns TCK-1005 (in addition to TCK-1001) | 200; `ticket_id` correct | ownership-positive | `tests/day2/test_05_week1_coverage.py::test_employee_a_retrieves_second_owned_ticket` |
| WK1-21 | Schema + data coverage | A `"resolved"`-status ticket (not just `"open"`/`"in_progress"`) conforms to schema | EMP002 owns TCK-1006 (`status: resolved`) | 200; `status == "resolved"`; full schema valid | schema | `tests/day2/test_05_week1_coverage.py::test_resolved_ticket_matches_schema` |
| WK1-22 | Observed behavior (not written in `docs/business_rules.md`) | A malformed ticket id (doesn't match the `TCK-<digits>` pattern) is treated the same as a missing ticket | EMP001 requests `"NOT-A-TICKET"` | 404 (same path as BR03, not a 422) | negative | `tests/day2/test_05_week1_coverage.py::test_malformed_ticket_id_returns_404_not_422` |

**Unique API scenario count: 22** (meets the ≥20 requirement).

**Raw pytest test count (verified by running the full suite, see below):
31**, i.e. `pytest`'s own count of test functions/parametrize cases
actually collected — deliberately a different, larger number than the 22
unique scenarios above, because it also counts overlapping teaching
demonstrations (6 of them) and the 2 non-API beginner validator examples
that the scenario count excludes:

| File | pytest tests | Of which: new unique scenarios | Of which: overlap/non-API |
| --- | --- | --- | --- |
| `tests/test_employees.py` | 1 | 1 (WK1-01) | 0 |
| `tests/test_tickets.py` | 3 | 3 (WK1-02, 03, 04) | 0 |
| `tests/test_service_status.py` | 2 | 2 (WK1-05, 06) | 0 |
| `tests/day2/test_01_fixtures.py` | 2 | 1 (WK1-07) | 1 (EMP001 own-ticket, overlaps WK1-02) |
| `tests/day2/test_02_parameterized.py` | 5 | 1 (WK1-09) | 4 (overlap WK1-02, WK1-07, WK1-08, WK1-03) |
| `tests/day2/test_03_ownership.py` | 2 | 1 (WK1-08) | 1 (overlaps WK1-03) |
| `tests/day2/test_04_schema.py` | 6 | 3 (WK1-10, 11, 12) | 3 (1 overlaps WK1-04; 2 are non-API beginner examples) |
| `tests/day2/test_05_week1_coverage.py` | 10 | 10 (WK1-13..WK1-22) | 0 |
| **Total** | **31** | **22** | **9** |

## Counting notes — what was deliberately excluded

Per the instructions for this matrix, the following are **not** counted
as separate scenarios, even though they exist as real pytest tests:

- **Repeated teaching demonstrations.** `test_01_fixtures.py`'s and
  `test_02_parameterized.py`'s own-ticket rows for EMP001, and
  `test_02`'s/`test_03`'s identical EMP002→EMP001 denial, restate cases
  already counted (WK1-02, WK1-03, WK1-07, WK1-08). `test_04_schema.py`'s
  ticket-schema test intentionally reuses the exact same schema and
  request as WK1-04, to demonstrate schema-file reuse, not to add
  coverage.
- **Individual assertions.** Each row above is one request with however
  many assertions it takes to check it; extra `assert` lines inside one
  test are not separate scenarios.
- **Standalone validator examples.** `test_04_schema.py`'s
  `test_beginner_example_required_field_missing` and
  `test_beginner_example_wrong_type` validate hand-written dicts against
  an inline toy schema with no HTTP call at all. They teach `jsonschema`
  keyword behavior and are excluded entirely.
- **Fault-injected reruns.** Running `test_03_ownership.py` with
  `--day2-fault=ownership`, or `test_04_schema.py` with
  `--day2-fault=missing-status` / `--day2-fault=wrong-status-type`, does
  not create new scenarios — it's the same scenario (WK1-08, WK1-11) run
  a second time to prove the check would catch a real regression. See
  `docs/day2-instructor-map.md`'s Lesson 3 and Lesson 4 sections for that
  verification.

## Documented unsupported coverage

This API does not implement the following, so no case exists for them
here — they were not invented to pad the count:

- **No write operations.** There is no `POST`/`PUT`/`PATCH`/`DELETE`
  anywhere (no ticket creation, update, resolution, or employee
  management). Only `GET` routes exist.
- **No ticket collection/listing endpoint.** Only
  `GET /tickets/{ticket_id}` exists — there is no `GET /tickets`, so
  pagination, filtering, and search cannot be exercised.
- **No query parameters or request bodies anywhere.** Nothing in this
  API accepts either, so query-param validation and request-body
  validation are not applicable.
- **No real authentication/authorization.** `X-Demo-Employee-ID` is a
  synthetic demo header, not a token or session; there is nothing to
  test for expiry, scopes, refresh, or roles beyond simple ticket
  ownership (BR02).
- **No rate limiting, pagination, caching headers, or API versioning.**
- **HTTP 405 (Method Not Allowed) on an existing route** (e.g. `POST
  /tickets/TCK-1001`) is real, testable behavior — FastAPI/Starlette
  generates it automatically for any route given an unsupported verb —
  but it exercises the framework's own routing, not a business rule or
  schema this project defines, so it is out of scope for this matrix and
  was not added merely to inflate the case count.
