# Day 2 Instructor Map

Reconnaissance notes for Day 2, recorded before any Day 2 tests were
written. This documents the existing Day 1 application and test suite as
they actually are, not as designed. Day 1 files are untouched.

## 1–2. Existing Day 1 test files (explicit paths)

- `tests/conftest.py` — shared `client` fixture (FastAPI `TestClient`)
- `tests/test_employees.py` — `GET /employees/me`
- `tests/test_tickets.py` — `GET /tickets/{ticket_id}`
- `tests/test_service_status.py` — `GET /health`, `GET /services/vpn/status`

## 3–4. Command to run only the Day 1 files (verified)

```bash
python -m pytest tests/test_employees.py tests/test_tickets.py tests/test_service_status.py -v
```

Verified 2026-09-27 with the project's `.venv` active
(`source .venv/bin/activate`, Python 3.12.7, pytest 8.4.2, fastapi
0.141.1). Result:

```
6 passed, 1 warning in 0.12s
```

The one warning is an unrelated `StarletteDeprecationWarning` about
`httpx`/`testclient`, not a failure.

## 5. Employee IDs, ticket ownership, endpoints, response fields, status codes

### Employee IDs (`data/employees.json`)

| employee_id | full_name | department |
| --- | --- | --- |
| EMP001 | Dana Whitfield | Finance |
| EMP002 | Marcus Lee | Sales |
| EMP003 | Priya Nair | Engineering |
| EMP004 | Oliver Grant | Human Resources |

Identity mechanism (BR01): the "current employee" comes only from the
`X-Demo-Employee-ID` request header (`app/main.py:get_current_employee`).
There is no real authentication — this is a synthetic demo header, never
inferred from body/query text.

### Ticket ownership (`data/tickets.json`)

| ticket_id | employee_id | status |
| --- | --- | --- |
| TCK-1001 | EMP001 | open |
| TCK-1002 | EMP002 | resolved |
| TCK-1003 | EMP003 | in_progress |
| TCK-1004 | EMP004 | open |
| TCK-1005 | EMP001 | in_progress |
| TCK-1006 | EMP002 | resolved |

Ownership check (BR02): `app/rules.py:employee_owns_ticket` — a ticket's
`employee_id` must equal the requesting employee's `employee_id`.

### Endpoints, response fields, expected status codes

| Endpoint | Auth header required | Success | Response fields | Error cases |
| --- | --- | --- | --- | --- |
| `GET /health` | No | 200 | `status`, `service` | — |
| `GET /employees/me` | Yes | 200 | `employee_id`, `full_name`, `department`, `email` | 400 missing header; 400 unknown employee id |
| `GET /services/vpn/status` | No | 200 | `service`, `status` (`operational`\|`degraded`\|`outage`), `updated_at`, `message` | — |
| `GET /tickets/{ticket_id}` | Yes | 200, matches `schemas/ticket.schema.json` | `ticket_id`, `employee_id`, `subject`, `description`, `status` (`open`\|`in_progress`\|`resolved`), `created_at`, `updated_at` | 400 missing/unknown header; 404 ticket not found (checked before ownership); 403 ticket belongs to a different employee |

Full rule text: `docs/business_rules.md` (BR01–BR04).

## 6. API startup command

Tests use FastAPI's `TestClient` directly against the `app` object
(`tests/conftest.py`), so **no running server is needed for the existing
or planned Day 2 test files**.

For manual/curl exploration only, if needed:

- macOS/Linux: `uvicorn app.main:app --reload --port 8000`
- Windows PowerShell: `uvicorn app.main:app --reload --port 8000`

(Note: README.md's macOS/Linux section currently just says `python` under
"Running the API locally" — that appears to be a doc error; the actual
command is the `uvicorn` one above, same as the Windows section.)

## 7. Baseline results and blockers

- Baseline Day 1 suite: **6 passed, 0 failed** (see command output above).
- No blockers. `.venv` was already present and had `fastapi`, `pytest`,
  `jsonschema`, etc. installed.
- Pre-existing, unrelated working-tree state (not touched by this
  reconnaissance): `pyproject.toml` has an uncommitted change commenting
  out the `requires-python` pin, and an empty untracked scratch file
  `practise-day1.py` exists at the repo root.

New Day 2 test files will go under `tests/day2/`. Day 1 test files above
are not being moved or renamed.

## Day 2, Lesson 1 — Fixtures (implemented 2026-09-27)

Files added:

- `tests/day2/conftest.py` — adds `employee_a_headers` and
  `employee_b_headers` fixtures. Both build on the existing `client`
  fixture from `tests/conftest.py` (pytest auto-discovers `conftest.py`
  up the directory tree, so nothing there needed to be redefined) and
  reuse the app's own `DEMO_HEADER_NAME` constant from `app/main.py`
  instead of hardcoding the header name again.
- `tests/day2/test_01_fixtures.py` — two tests:
  - `test_employee_a_retrieves_own_ticket`: EMP001 (Employee A) fetches
    TCK-1001.
  - `test_employee_b_retrieves_own_ticket`: EMP002 (Employee B) fetches
    TCK-1002.

Expected ownership (EMP001 → TCK-1001, EMP002 → TCK-1002) was taken from
`data/tickets.json` directly, not from the API response under test, and
each test asserts status code 200, the requested `ticket_id`, and the
expected `employee_id` owner.

Command run (new file + all recorded Day 1 files):

```bash
python -m pytest tests/day2/test_01_fixtures.py tests/test_employees.py tests/test_tickets.py tests/test_service_status.py -v
```

Verified 2026-09-27, same `.venv` as the Day 1 baseline run above. Result:

```
8 passed, 1 warning in 0.16s
```

The one warning is the same pre-existing, unrelated
`StarletteDeprecationWarning` noted in the Day 1 baseline — not caused by
the new fixtures file. No blockers.

## Day 2, Lesson 2 — Parameterised tests (implemented 2026-09-27)

File added: `tests/day2/test_02_parameterized.py`. No new fixtures — it
reuses `client` (tests/conftest.py) and `employee_a_headers` /
`employee_b_headers` (tests/day2/conftest.py) via
`request.getfixturevalue(name)`.

One parameterised test function, `test_ticket_access_matrix`, run across
5 rows (pytest reports each as its own test result, named by its `id=`):

| Case id | Requester | Ticket | Expected status | Checked |
| --- | --- | --- | --- | --- |
| `employee_a_own_ticket__overlaps_test_01_fixtures` | EMP001 | TCK-1001 (own) | 200 | `ticket_id`, `employee_id` |
| `employee_b_own_ticket__overlaps_test_01_fixtures` | EMP002 | TCK-1002 (own) | 200 | `ticket_id`, `employee_id` |
| `employee_a_requests_employee_b_ticket_denied` | EMP001 | TCK-1002 (EMP002's) | 403 | no ticket fields in body; EMP002's ticket subject absent from response text |
| `employee_b_requests_employee_a_ticket_denied` | EMP002 | TCK-1001 (EMP001's) | 403 | no ticket fields in body; EMP001's ticket subject absent from response text |
| `valid_employee_requests_missing_wellformed_ticket` | EMP001 | TCK-9999 (well-formed, absent) | 404 | no ticket fields in body |

**Overlap / unique-case accounting:** the first two rows above duplicate
the two tests already in `tests/day2/test_01_fixtures.py` (own-ticket
retrieval by Employee A and Employee B) — kept here only so the
parameterised table reads as one complete access-control contract. They
do not count as new coverage. Net new unique cases introduced by this
lesson: **3** (the two 403 cross-access denials and the 404
well-formed-but-missing case). Total distinct behaviours verified across
`test_01_fixtures.py` + `test_02_parameterized.py` so far: **5** (own
ticket ×2, cross-employee denial ×2, missing ticket ×1).

All expected values (owners, subjects, status codes) were fixed from
`data/tickets.json` and `app/main.py` before running, not derived from
the responses under test, and every status-code assertion checks for the
one exact code — no alternative/range acceptance.

Command run (new file + fixtures lesson + all recorded Day 1 files):

```bash
python -m pytest tests/day2/test_02_parameterized.py tests/day2/test_01_fixtures.py tests/test_employees.py tests/test_tickets.py tests/test_service_status.py -v
```

Verified 2026-09-27, same `.venv`. Result:

```
13 passed, 1 warning in 0.19s
```

Same pre-existing, unrelated `httpx`/`StarletteDeprecationWarning` as
before. No blockers.

## Day 2, Lesson 3 — Ownership fault injection (implemented 2026-09-27)

Files touched:

- `tests/day2/conftest.py` — added `pytest_addoption`, registering a
  TEST-ONLY CLI flag: `--day2-fault` (currently accepts only
  `ownership`, default `None`). Registering the option by itself does
  nothing; it only has an effect on a test that explicitly reads it.
- `tests/day2/test_03_ownership.py` (new) — two cross-employee-access
  tests (EMP001 → EMP002's ticket, EMP002 → EMP001's ticket), each
  requesting the local `ownership_fault` fixture defined in that same
  file.

**Enforcement location (BR02):** `app/rules.py:employee_owns_ticket` is
the single function that decides ticket ownership. `app/main.py`'s
`GET /tickets/{ticket_id}` route calls it directly as a plain function
call — unlike `get_current_employee`, which is wired in via FastAPI's
`Depends(...)` and is swappable through `app.dependency_overrides`, the
ownership check has no such injection seam.

**Why monkeypatch instead of a second app instance:** because there is
no `Depends(...)` seam for the ownership check, `app.dependency_overrides`
cannot target it. The safe substitute is pytest's built-in `monkeypatch`
fixture, which replaces `app.rules.employee_owns_ticket` with a
fake `lambda ticket, employee_id: True` for the duration of one test
only, then automatically restores the original function when that test
ends — pass or fail. This does not touch authentication
(`get_current_employee`), any file in `data/`, or the app when run
outside pytest. Isolated injection turned out to be supported by this
architecture, so no blocker is being reported for this lesson.

**Blast-radius control:** the fault fixture (`ownership_fault`) is local
to `test_03_ownership.py` and is only applied to a test that explicitly
requests it as a parameter — it is not `autouse`. Verified: running
`pytest tests/day2/ --day2-fault=ownership` fails only the 2 tests in
`test_03_ownership.py`; the 2 tests in `test_01_fixtures.py` and all 5 in
`test_02_parameterized.py` still pass unaffected (7 passed, 2 failed).

**3-step verification (all run 2026-09-27, same `.venv`):**

1. Normal run — enforcement is real:
   `python -m pytest tests/day2/test_03_ownership.py -v` → **2 passed**.
2. Fault-injected run — same test code, unchanged, proves the tests are
   not vacuous:
   `python -m pytest tests/day2/test_03_ownership.py -v --day2-fault=ownership`
   → **2 failed**, both on `assert response.status_code == 403` (actual:
   `200`), because BR02 was bypassed. Not marked `xfail` — genuine
   failures, as required.
3. Normal run again — proves no leakage between runs:
   `python -m pytest tests/day2/test_03_ownership.py -v` → **2 passed**
   again, identical to step 1.

Full recorded-suite command (normal mode, no fault flag):

```bash
python -m pytest tests/day2/test_03_ownership.py tests/day2/test_02_parameterized.py tests/day2/test_01_fixtures.py tests/test_employees.py tests/test_tickets.py tests/test_service_status.py -v
```

Result: **15 passed, 1 warning** (same pre-existing, unrelated `httpx`
deprecation warning as before). No blockers.

## Day 2, Lesson 4 — Reusable JSON Schema validation (implemented 2026-09-27)

Files added:

- `schemas/employee_profile.schema.json` (new) — GET `/employees/me`.
- `schemas/service_status.schema.json` (new) — GET `/services/vpn/status`
  (BR04: requires `service`, `status` enum, `updated_at`; `message` is
  present but not required, matching what BR04 actually guarantees).
- `schemas/error_response.schema.json` (new) — the generic
  `{"detail": "..."}` body FastAPI's `HTTPException` produces.
- `schemas/ticket.schema.json` — **not** duplicated; Day 1's existing
  schema is reused as-is.
- `tests/day2/conftest.py` — added `assert_matches_schema`, a reusable
  fixture-factory: it returns a function each test calls as
  `assert_matches_schema(body, "some_schema.json")`, so the
  open-file/load/validate steps are written once, not per test.
- `tests/day2/test_04_schema.py` (new) — 4 real API cases + 2 explicitly
  non-API "beginner validator" examples (see below).

**Dependency file:** `jsonschema>=4.21,<5.0` was already declared in
`pyproject.toml` (added in Day 1 for `tests/test_tickets.py`; installed
version confirmed as 4.26.0). No edit was needed or made — reused as-is.

**Status-before-schema ordering:** every test asserts the exact HTTP
status code first, and only calls `assert_matches_schema` on the body
afterward, so a wrong status can never be masked by (or confused with) a
schema check on the wrong kind of body.

**4 real API cases:**

| Case | Request | Expected status | Schema |
| --- | --- | --- | --- |
| Employee profile | `GET /employees/me` as EMP001 | 200 | `employee_profile.schema.json` |
| Ticket | `GET /tickets/TCK-1001` as EMP001 (owner) | 200 | `ticket.schema.json` (Day 1's, reused) |
| Service status | `GET /services/vpn/status` | 200 | `service_status.schema.json` |
| Relevant error response (BR03) | `GET /tickets/TCK-9999` (well-formed, missing) as EMP001 | 404 | `error_response.schema.json` |

**Beginner validator examples (explicitly not counted as API cases):**
`test_beginner_example_required_field_missing` and
`test_beginner_example_wrong_type` validate small hand-written dicts
against a tiny inline `TOY_SCHEMA` — no HTTP call, no app involved. They
exist only to show `required` and `"type": "string"` failing in
isolation, and are excluded from this lesson's API-case count for the
same reason test_02's overlapping rows were excluded in Lesson 2.

**Fault injection: `missing-status` / `wrong-status-type`** (extends the
same `--day2-fault` option from Lesson 3, registered in
`tests/day2/conftest.py`; choices are now `["ownership", "missing-status",
"wrong-status-type"]`):

- **Where generated:** `app/data.py:load_service_status()`, called
  directly (no `Depends(...)` seam) by `app/main.py`'s
  `GET /services/vpn/status` route.
- **How injected:** the `service_status_fault` fixture in
  `test_04_schema.py` monkeypatches `app.data.load_service_status` itself
  — the response-generation source — to return a copy of the real data
  with `status` removed (`missing-status`) or set to the integer `123`
  (`wrong-status-type`). `data/service_status.json` on disk is never
  touched, and `monkeypatch` auto-restores the real function once the
  requesting test ends.
- **Does FastAPI's own response validation catch it first? No.**
  `get_vpn_status()` is annotated `-> dict` (no `response_model`, no
  Pydantic model), so FastAPI performs no response-shape validation at
  all for this route. Confirmed by running both faults: the API still
  answers `200 OK` with the malformed body untouched in both cases; it is
  `assert_matches_schema` in this test file — not FastAPI — that raises.
  This is why the JSON Schema check is a real safety net here, not a
  redundant re-check of something the framework already guarantees.

**4-step verification (all run 2026-09-27, same `.venv`, command:
`python -m pytest tests/day2/test_04_schema.py -v [--day2-fault=...]`):**

1. Baseline: **6 passed**.
2. `--day2-fault=missing-status`: **1 failed, 5 passed**. Failure:
   `jsonschema.exceptions.ValidationError: 'status' is a required property`
   on `test_service_status_matches_schema`. Not `xfail` — a genuine
   failure.
3. `--day2-fault=wrong-status-type`: **1 failed, 5 passed**. Failure:
   `jsonschema.exceptions.ValidationError: 123 is not of type 'string'`
   on the same test. Not `xfail`.
4. Baseline again: **6 passed** — no leakage between runs.

**Blast-radius check:** `pytest tests/day2/ --day2-fault=wrong-status-type`
→ **14 passed, 1 failed** — only `test_service_status_matches_schema`
fails; every test in `test_01_fixtures.py`, `test_02_parameterized.py`,
and `test_03_ownership.py` is unaffected.

Full recorded-suite command (normal mode, no fault flag):

```bash
python -m pytest tests/day2/test_04_schema.py tests/day2/test_03_ownership.py tests/day2/test_02_parameterized.py tests/day2/test_01_fixtures.py tests/test_employees.py tests/test_tickets.py tests/test_service_status.py -v
```

Result: **21 passed, 1 warning** (same pre-existing, unrelated `httpx`
deprecation warning as before). No blockers.

## Day 2, Lesson 5 — Week 1 API case matrix + gap-fill (implemented 2026-10-03)

New deliverable: `docs/week01-api-case-matrix.md`. It reviews every test
across Day 1 and Day 2 Lessons 1–4 and catalogs each **unique** API
scenario (not every pytest test — repeated teaching demonstrations,
individual assertions, the 2 non-API beginner validator examples from
Lesson 4, and fault-injected reruns are explicitly excluded, with a
"Counting notes" section explaining each exclusion).

That review found only **12** unique scenarios already covered
(cases WK1-01..WK1-12), short of the required 20. The gap was closed by
adding `tests/day2/test_05_week1_coverage.py` — 10 new tests, cases
WK1-13..WK1-22, using only endpoints, fields, and synthetic employees
already present in this project (no invented endpoints):

- BR01 negatives never tested before: missing header (on both
  `/employees/me` and `/tickets/{id}`, showing the shared auth dependency
  applies to both routes) and an unknown employee id.
- EMP003 and EMP004 — real employees in `data/employees.json` that no
  earlier Day 2 lesson had ever used — each retrieving their own ticket,
  plus a brand-new cross-ownership denial pair (EMP003 → EMP004's
  ticket) that isn't just the same EMP001/EMP002 pair tested yet again.
- EMP001's *second* ticket (TCK-1005), proving ownership is checked per
  ticket, not hardcoded to the one ticket id every earlier test happened
  to use.
- A `"resolved"`-status ticket (TCK-1006) validated against the schema —
  every prior schema/ticket test used an `"open"` or `"in_progress"`
  ticket.
- An observed-but-undocumented behavior: a malformed ticket id (doesn't
  match the `TCK-<digits>` pattern) is treated identically to a
  well-formed-but-missing one (404), not rejected separately with a 422
  — the API has no format-validation step at all for this path param.

Fixtures added to `tests/day2/conftest.py` for this file:
`employee_c_headers` (EMP003), `employee_d_headers` (EMP004),
`unknown_employee_headers` (a made-up "EMP999") — all following the
exact pattern already used by `employee_a_headers`/`employee_b_headers`.

**Documented unsupported coverage** (see the matrix's own section): this
API has no write endpoints, no ticket-listing/collection endpoint, no
query params or request bodies anywhere, no real auth beyond the demo
header, and no rate limiting/pagination/versioning — so none of those
have a case here. HTTP 405 on an existing route was noted as real,
testable framework behavior that was deliberately left out as out of
scope (it tests Starlette's routing, not this project's own rules).

**Day 1 preserved:** `tests/test_employees.py`, `tests/test_tickets.py`,
and `tests/test_service_status.py` were not modified.

**Unique API scenario count vs. raw pytest count (explicitly reported
separately, per the task):**
- **22** unique API scenarios (WK1-01..WK1-22) — exceeds the ≥20
  requirement.
- **31** raw pytest tests actually collected across all of Day 1 + Day
  2 — a different, larger number on purpose; see the breakdown table in
  `docs/week01-api-case-matrix.md` for exactly which tests are overlap
  or non-API per file.

**Baseline run** (`python -m pytest tests/ -v`, 2026-10-03, same
`.venv`): **31 passed, 1 warning** (same pre-existing, unrelated `httpx`
deprecation warning as before). No blockers.
