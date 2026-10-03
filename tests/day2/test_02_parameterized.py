"""
Day 2, Lesson 2: Parameterised tests.

What "parameterised" means here, in plain language:

Instead of writing one test function per case (like test_01_fixtures.py
does), `@pytest.mark.parametrize(...)` lets one test function run several
times, once per row of a table we hand it. Each row supplies the inputs
for that run (which employee, which ticket) and the outcome we expect
(status code, expected owner). pytest reports every row as its own
separate test result, using the `id=` string we give it, so a failure in
one row still tells you exactly which case broke.

Fixtures reused (no new fixtures added in this file):
- `client` from tests/conftest.py
- `employee_a_headers` / `employee_b_headers` from tests/day2/conftest.py

A parametrize row can only carry plain values (strings, numbers, etc.),
not a fixture directly. So each row carries the *name* of the headers
fixture to use ("employee_a_headers" or "employee_b_headers"), and the
test body calls `request.getfixturevalue(name)` to fetch that fixture's
actual value at run time. `request` here is pytest's own built-in
fixture for introspecting the current test, not an HTTP request.

Overlap with tests/day2/test_01_fixtures.py:
The first two rows below ("employee_a_own_ticket", "employee_b_own_ticket")
exercise the same behaviour already covered there (Employee A / Employee B
retrieving their own ticket). They are included here to keep this table a
complete, readable contract for ticket access, but they are NOT additional
unique coverage — see docs/day2-instructor-map.md for the deduplicated
case count.

Ticket ownership used below (data/tickets.json):
- TCK-1001 belongs to EMP001 (Employee A), subject "VPN client fails to
  connect from home network".
- TCK-1002 belongs to EMP002 (Employee B), subject "VPN password reset
  needed".
- TCK-9999 does not exist in data/tickets.json, but it is a well-formed
  ticket id (matches the "TCK-<digits>" pattern in
  schemas/ticket.schema.json).
"""

import pytest

EMPLOYEE_A_ID = "EMP001"
EMPLOYEE_A_TICKET_ID = "TCK-1001"
EMPLOYEE_A_TICKET_SUBJECT = "VPN client fails to connect from home network"

EMPLOYEE_B_ID = "EMP002"
EMPLOYEE_B_TICKET_ID = "TCK-1002"
EMPLOYEE_B_TICKET_SUBJECT = "VPN password reset needed"

MISSING_BUT_WELLFORMED_TICKET_ID = "TCK-9999"


@pytest.mark.parametrize(
    "requester_fixture_name, ticket_id, expected_status, expected_owner_id, foreign_subject_must_be_absent",
    [
        pytest.param(
            "employee_a_headers",
            EMPLOYEE_A_TICKET_ID,
            200,
            EMPLOYEE_A_ID,
            None,
            id="employee_a_own_ticket__overlaps_test_01_fixtures",
        ),
        pytest.param(
            "employee_b_headers",
            EMPLOYEE_B_TICKET_ID,
            200,
            EMPLOYEE_B_ID,
            None,
            id="employee_b_own_ticket__overlaps_test_01_fixtures",
        ),
        pytest.param(
            "employee_a_headers",
            EMPLOYEE_B_TICKET_ID,
            403,
            None,
            EMPLOYEE_B_TICKET_SUBJECT,
            id="employee_a_requests_employee_b_ticket_denied",
        ),
        pytest.param(
            "employee_b_headers",
            EMPLOYEE_A_TICKET_ID,
            403,
            None,
            EMPLOYEE_A_TICKET_SUBJECT,
            id="employee_b_requests_employee_a_ticket_denied",
        ),
        pytest.param(
            "employee_a_headers",
            MISSING_BUT_WELLFORMED_TICKET_ID,
            404,
            None,
            None,
            id="valid_employee_requests_missing_wellformed_ticket",
        ),
    ],
)
def test_ticket_access_matrix(
    request,
    client,
    requester_fixture_name,
    ticket_id,
    expected_status,
    expected_owner_id,
    foreign_subject_must_be_absent,
):
    # Arrange: look up the actual headers fixture (employee_a_headers or
    # employee_b_headers) by the name this row supplied, and remember which
    # ticket we're about to ask for.
    headers = request.getfixturevalue(requester_fixture_name)

    # Act: make the one real API call this case is testing.
    response = client.get(f"/tickets/{ticket_id}", headers=headers)

    # Assert: the exact status code this case expects -- never a range or
    # a set of "acceptable" codes.
    assert response.status_code == expected_status
    body = response.json()

    if expected_status == 200:
        # Own ticket: the full ticket comes back, and its owner is the
        # employee we expected before making the call (from
        # data/tickets.json, not read back from this response).
        assert body["ticket_id"] == ticket_id
        assert body["employee_id"] == expected_owner_id
    else:
        # Denied (403) or missing (404): only an error message, never any
        # ticket content. This is what stops a denied or not-found request
        # from leaking protected foreign-ticket data.
        assert "ticket_id" not in body
        assert "employee_id" not in body
        assert "subject" not in body
        assert "description" not in body
        assert "detail" in body

        if foreign_subject_must_be_absent is not None:
            assert foreign_subject_must_be_absent not in response.text
