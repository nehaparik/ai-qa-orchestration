"""
Day 2, Lesson 5: Week 1 API case-matrix gap-fill.

docs/week01-api-case-matrix.md reviewed every test across Day 1
(tests/test_employees.py, tests/test_tickets.py,
tests/test_service_status.py) and Day 2 Lessons 1-4
(tests/day2/test_01_fixtures.py .. test_04_schema.py) and found the
unique API scenarios already covered (cases WK1-01..WK1-12 in that
matrix). This file adds the real, meaningful gaps that review turned up
(cases WK1-13..WK1-22) -- it does not repeat anything already covered
above, and it only uses endpoints, fields, and synthetic data that
already exist in this project (app/main.py, data/employees.json,
data/tickets.json). Each test below is commented with its case ID so it
can be matched back to that matrix.

Fixtures reused from tests/day2/conftest.py:
- `client` (via tests/conftest.py)
- `employee_a_headers` (EMP001), `employee_c_headers` (EMP003),
  `employee_d_headers` (EMP004) -- `employee_c_headers` and
  `employee_d_headers` were added alongside this file, following the
  exact same pattern as the existing `employee_a_headers` /
  `employee_b_headers`.
- `unknown_employee_headers` (a made-up id, "EMP999", that does not
  exist in data/employees.json) -- also added alongside this file.
- `assert_matches_schema` (from Lesson 4).

Employee/ticket data used below (data/employees.json, data/tickets.json):
- EMP003 = Priya Nair, owns TCK-1003.
- EMP004 = Oliver Grant, owns TCK-1004.
- EMP001 (already used elsewhere as Employee A) also owns a *second*
  ticket, TCK-1005 (status "in_progress") -- it is not the same ticket
  as TCK-1001.
- EMP002 (already used elsewhere as Employee B) also owns TCK-1006,
  which has status "resolved" -- every other ticket exercised so far in
  Week 1 was "open" or "in_progress".
"""

EMPLOYEE_A_ID = "EMP001"
EMPLOYEE_A_SECOND_TICKET_ID = "TCK-1005"

EMPLOYEE_B_ID = "EMP002"
EMPLOYEE_B_RESOLVED_TICKET_ID = "TCK-1006"

EMPLOYEE_C_ID = "EMP003"
EMPLOYEE_C_TICKET_ID = "TCK-1003"

EMPLOYEE_D_ID = "EMP004"
EMPLOYEE_D_TICKET_ID = "TCK-1004"

MALFORMED_TICKET_ID = "NOT-A-TICKET"  # doesn't match the "TCK-<digits>" pattern at all


# WK1-13
def test_missing_header_on_profile_returns_400(client):
    # Arrange: no X-Demo-Employee-ID header at all (BR01).
    # Act
    response = client.get("/employees/me")

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Missing required header: X-Demo-Employee-ID"}


# WK1-14
def test_unknown_employee_id_on_profile_returns_400(client, unknown_employee_headers):
    # Arrange: EMP999 is not in data/employees.json (BR01).
    # Act
    response = client.get("/employees/me", headers=unknown_employee_headers)

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Unknown demo employee id: EMP999"}


# WK1-15
def test_missing_header_on_ticket_endpoint_returns_400(client):
    # Arrange: no header, requesting a ticket that does exist (TCK-1001).
    # This shows get_current_employee's BR01 check runs -- and rejects
    # the request -- before the route ever reaches the BR02 ownership
    # check, on this endpoint too, not just /employees/me.
    ticket_id = "TCK-1001"

    # Act
    response = client.get(f"/tickets/{ticket_id}")

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Missing required header: X-Demo-Employee-ID"}


# WK1-16
def test_employee_c_retrieves_own_profile(client, employee_c_headers):
    # Arrange: Employee C is EMP003 (Priya Nair), a real employee that no
    # earlier Day 2 lesson exercised.
    # Act
    response = client.get("/employees/me", headers=employee_c_headers)

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["employee_id"] == EMPLOYEE_C_ID
    assert body["full_name"] == "Priya Nair"


# WK1-17
def test_employee_c_retrieves_own_ticket(client, employee_c_headers):
    # Arrange: TCK-1003 belongs to Employee C (EMP003).
    ticket_id = EMPLOYEE_C_TICKET_ID

    # Act
    response = client.get(f"/tickets/{ticket_id}", headers=employee_c_headers)

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["ticket_id"] == ticket_id
    assert body["employee_id"] == EMPLOYEE_C_ID


# WK1-18
def test_employee_d_retrieves_own_ticket(client, employee_d_headers):
    # Arrange: TCK-1004 belongs to Employee D (EMP004).
    ticket_id = EMPLOYEE_D_TICKET_ID

    # Act
    response = client.get(f"/tickets/{ticket_id}", headers=employee_d_headers)

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["ticket_id"] == ticket_id
    assert body["employee_id"] == EMPLOYEE_D_ID


# WK1-19
def test_employee_c_cannot_view_employee_ds_ticket(client, employee_c_headers):
    # Arrange: TCK-1004 belongs to Employee D (EMP004), not Employee C.
    # Earlier ownership-denial tests only ever used the EMP001/EMP002
    # pair; this proves BR02 also holds for a pair that was never tested
    # before.
    ticket_id = EMPLOYEE_D_TICKET_ID

    # Act
    response = client.get(f"/tickets/{ticket_id}", headers=employee_c_headers)

    # Assert: denied, and Employee D's actual ticket content is not leaked.
    assert response.status_code == 403
    body = response.json()
    assert body == {"detail": "You may not view another employee's ticket."}
    assert "ticket_id" not in body
    assert "employee_id" not in body


# WK1-20
def test_employee_a_retrieves_second_owned_ticket(client, employee_a_headers):
    # Arrange: Employee A (EMP001) owns two tickets -- TCK-1001 (already
    # exercised elsewhere) and TCK-1005. This proves ownership is checked
    # per-ticket against data/tickets.json, not hardcoded to whichever
    # single ticket earlier tests happened to use.
    ticket_id = EMPLOYEE_A_SECOND_TICKET_ID

    # Act
    response = client.get(f"/tickets/{ticket_id}", headers=employee_a_headers)

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["ticket_id"] == ticket_id
    assert body["employee_id"] == EMPLOYEE_A_ID


# WK1-21
def test_resolved_ticket_matches_schema(client, employee_b_headers, assert_matches_schema):
    # Arrange: TCK-1006 belongs to Employee B (EMP002) and has status
    # "resolved" -- every other ticket exercised in Week 1 so far was
    # "open" or "in_progress", so this is the first check that the
    # schema's status enum also accepts "resolved" on a real response.
    ticket_id = EMPLOYEE_B_RESOLVED_TICKET_ID

    # Act
    response = client.get(f"/tickets/{ticket_id}", headers=employee_b_headers)

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "resolved"
    assert_matches_schema(body, "ticket.schema.json")


# WK1-22
def test_malformed_ticket_id_returns_404_not_422(client, employee_a_headers):
    # Arrange: "NOT-A-TICKET" doesn't match the "TCK-<digits>" pattern
    # that schemas/ticket.schema.json documents for ticket_id -- but the
    # route has no separate format-validation step. This is an observed
    # behavior (not written in docs/business_rules.md): a malformed id
    # is treated exactly like a well-formed-but-missing one (BR03), not
    # rejected earlier with a 422.
    ticket_id = MALFORMED_TICKET_ID

    # Act
    response = client.get(f"/tickets/{ticket_id}", headers=employee_a_headers)

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": f"Ticket not found: {ticket_id}"}
