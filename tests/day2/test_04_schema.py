"""
Day 2, Lesson 4: Reusable JSON Schema validation.

What JSON Schema is checking, in beginner language (the four keywords
this lesson asked to have explained):

- `"type": "object"` at the top level means "this JSON value must be a
  `{...}` object (named fields), not a list, a plain string, or a number."
  Every response body validated below is checked against a schema whose
  top-level `"type"` is `"object"`.
- `"properties"` is a dictionary describing each field we care about
  *inside* that object -- one entry per field name, each with its own
  rules (its own `"type"`, and sometimes more, like a `"pattern"` or an
  `"enum"` of allowed values).
- `"required"` is a plain list of field names that MUST be present in the
  object. If any of those keys is missing from the response body,
  validation fails -- this is exactly how the "missing-status" fault
  below gets caught.
- `"type": "string"` on one specific property means "this field's value
  must be JSON text," e.g. `"operational"`, not a number like `123` or a
  boolean. This is exactly how the "wrong-status-type" fault below gets
  caught.

`jsonschema.validate(instance=..., schema=...)` (from the `jsonschema`
package) is what actually checks all of this; it raises
`jsonschema.exceptions.ValidationError` the first time something doesn't
match.

Reusable validator used in every real test below:
`assert_matches_schema` is a fixture defined in `tests/day2/conftest.py`.
It is a "fixture factory" -- it returns a function, so every test in this
file can call `assert_matches_schema(body, "some_schema.json")` instead
of repeating "open the schema file, load it, call jsonschema.validate"
four separate times. This is the same reuse idea test_01_fixtures.py
introduced with `employee_a_headers` / `employee_b_headers`, applied to
schema validation instead of auth headers.

Order matters in every test below: **the HTTP status code is asserted
first**, and the schema is only applied to the body afterward. A 200
response and a 404 response have different, unrelated shapes (a ticket
vs. an error message) -- validating the wrong schema against the wrong
status would either fail for the wrong reason or (worse) pass by
accident.

Schemas used (all in `schemas/`):
- `employee_profile.schema.json` (new) -- GET /employees/me.
- `ticket.schema.json` (already existed, from Day 1's
  `tests/test_tickets.py`) -- GET /tickets/{ticket_id}, reused as-is here
  to show the same schema file can back more than one test file.
- `service_status.schema.json` (new) -- GET /services/vpn/status (BR04).
- `error_response.schema.json` (new) -- the generic `{"detail": "..."}`
  body FastAPI's HTTPException produces; exercised here via BR03's 404
  ("relevant error response" = a missing ticket, TCK-9999).

Dependency note: `jsonschema>=4.21,<5.0` is already declared in
`pyproject.toml` (installed version confirmed: 4.26.0) -- it was added in
Day 1 for `tests/test_tickets.py` and is reused as-is here. No dependency
file change was needed.

--- Fault injection: missing-status / wrong-status-type ---

Where the VPN status response is actually generated:
`app/data.py:load_service_status()` reads `data/service_status.json` and
returns it as a dict. `app/main.py`'s `GET /services/vpn/status` route
(`get_vpn_status`) calls `data.load_service_status()` directly and
returns whatever it gets, completely unchanged.

Why this is the fault-injection target, and why by monkeypatch:
Exactly as in test_03_ownership.py, this route has no `Depends(...)` seam
to swap out with `app.dependency_overrides` -- `data.load_service_status`
is a plain function call. So the `service_status_fault` fixture below
monkeypatches `app.data.load_service_status` itself (the
response-generation source), not the HTTP response object after the
test already received it. `monkeypatch` restores the real function
automatically once the requesting test ends, so nothing leaks to another
test, and `data/service_status.json` on disk is never touched.

Does FastAPI's own response validation catch either fault first?
No. `get_vpn_status()` is annotated `-> dict` (a bare dict, not a Pydantic
model or an explicit `response_model=...`), so FastAPI performs no
response-shape validation at all for this route -- it just serializes
whatever dict it receives. This was confirmed by running both faults: in
each case the API still answers `200 OK` and hands back the malformed
body untouched; it is `assert_matches_schema` in this test file, not
FastAPI, that raises the failure. That is the actual reason this lesson's
JSON Schema check is a meaningful safety net here, rather than a
redundant re-check of something the framework already guarantees.

How to run the fault demonstration (test code is unchanged between runs):

1. Baseline: `python -m pytest tests/day2/test_04_schema.py -v`
   Expected: all tests PASS.
2. `python -m pytest tests/day2/test_04_schema.py -v --day2-fault=missing-status`
   Expected: `test_service_status_matches_schema` FAILS with a
   `ValidationError` about the missing required `"status"` property (the
   other tests in this file are unaffected and still pass).
3. `python -m pytest tests/day2/test_04_schema.py -v --day2-fault=wrong-status-type`
   Expected: `test_service_status_matches_schema` FAILS with a
   `ValidationError` about `"status"` not being of type `"string"`.
4. Baseline again: `python -m pytest tests/day2/test_04_schema.py -v`
   Expected: PASS again, identical to step 1 -- proving neither fault
   leaked between runs.

Neither failure above is marked `xfail`; both are genuine assertion
failures, which is what proves the schema check would catch a real
regression.
"""

import pytest

from app import data

EMPLOYEE_A_ID = "EMP001"
EMPLOYEE_A_TICKET_ID = "TCK-1001"

MISSING_BUT_WELLFORMED_TICKET_ID = "TCK-9999"


@pytest.fixture()
def service_status_fault(request, monkeypatch):
    """Corrupt the VPN status response at its source, but only when asked.

    Reads the `--day2-fault` option (registered in tests/day2/conftest.py).
    If it is not "missing-status" or "wrong-status-type", this fixture
    does nothing -- `app.data.load_service_status` keeps running
    unmodified, and reads the real `data/service_status.json`.
    """
    fault = request.config.getoption("--day2-fault")

    if fault == "missing-status":
        real_status = data.load_service_status()
        faulty_status = {key: value for key, value in real_status.items() if key != "status"}
        monkeypatch.setattr(data, "load_service_status", lambda: faulty_status)
    elif fault == "wrong-status-type":
        real_status = data.load_service_status()
        faulty_status = dict(real_status)
        faulty_status["status"] = 123  # wrong type: should be a string, not an int
        monkeypatch.setattr(data, "load_service_status", lambda: faulty_status)

    return fault


def test_employee_profile_matches_schema(client, employee_a_headers, assert_matches_schema):
    # Arrange: Employee A (EMP001) is a real employee (data/employees.json).
    # Act
    response = client.get("/employees/me", headers=employee_a_headers)

    # Assert: status code first, then shape.
    assert response.status_code == 200
    assert_matches_schema(response.json(), "employee_profile.schema.json")


def test_ticket_matches_schema(client, employee_a_headers, assert_matches_schema):
    # Arrange: TCK-1001 belongs to Employee A (data/tickets.json).
    ticket_id = EMPLOYEE_A_TICKET_ID

    # Act
    response = client.get(f"/tickets/{ticket_id}", headers=employee_a_headers)

    # Assert: status code first, then shape -- reusing Day 1's own
    # schemas/ticket.schema.json, unmodified.
    assert response.status_code == 200
    assert_matches_schema(response.json(), "ticket.schema.json")


def test_service_status_matches_schema(client, assert_matches_schema, service_status_fault):
    # Arrange: GET /services/vpn/status needs no auth header (BR04).
    # Act
    response = client.get("/services/vpn/status")

    # Assert: status code first, then shape.
    assert response.status_code == 200
    assert_matches_schema(response.json(), "service_status.schema.json")


def test_missing_ticket_error_matches_schema(client, employee_a_headers, assert_matches_schema):
    # Arrange: TCK-9999 is well-formed (matches ticket.schema.json's
    # ticket_id pattern) but does not exist in data/tickets.json (BR03).
    ticket_id = MISSING_BUT_WELLFORMED_TICKET_ID

    # Act
    response = client.get(f"/tickets/{ticket_id}", headers=employee_a_headers)

    # Assert: status code first, then shape -- this is the "relevant
    # error response" case: a documented 404 with the generic error body.
    assert response.status_code == 404
    assert_matches_schema(response.json(), "error_response.schema.json")


# --- Beginner validator examples (NOT API tests) ---
#
# These two functions validate small, hand-written Python dictionaries
# against a tiny inline schema -- there is no HTTP call and no app
# involved. They exist purely to show `required`, `properties`,
# `"type": "object"`, and `"type": "string"` behaving in isolation, with
# nothing else going on. They are intentionally NOT counted as API test
# cases in docs/day2-instructor-map.md's case tally -- only the four
# tests above (employee profile, ticket, service status, error response)
# count as this lesson's real API coverage.

TOY_SCHEMA = {
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {"type": "string"},
    },
}


def test_beginner_example_required_field_missing():
    import jsonschema

    # A dict with no "name" key at all violates TOY_SCHEMA's "required".
    toy_payload = {"age": 30}

    with pytest.raises(jsonschema.exceptions.ValidationError, match="'name' is a required property"):
        jsonschema.validate(instance=toy_payload, schema=TOY_SCHEMA)


def test_beginner_example_wrong_type():
    import jsonschema

    # "name" is present, but it's a number, not the required string.
    toy_payload = {"name": 12345}

    with pytest.raises(jsonschema.exceptions.ValidationError, match="is not of type 'string'"):
        jsonschema.validate(instance=toy_payload, schema=TOY_SCHEMA)
