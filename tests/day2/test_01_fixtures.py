"""
Day 2, Lesson 1: Fixtures.

Fixtures used in this file, and where they come from:

- `client` — defined in tests/conftest.py. A FastAPI TestClient wired to
  the app, with no real network calls. Shared by every test in the whole
  suite (Day 1 and Day 2).
- `employee_a_headers` / `employee_b_headers` — defined in
  tests/day2/conftest.py. Each returns the X-Demo-Employee-ID header for
  one specific, real employee (see app/main.py for how the app reads
  that header, and data/employees.json for the employee records).

Ticket ownership used below (data/tickets.json):
- TCK-1001 belongs to EMP001 (Employee A).
- TCK-1002 belongs to EMP002 (Employee B).

Files to open alongside this test:
- app/main.py       (the /tickets/{ticket_id} route and get_current_employee)
- app/rules.py      (employee_owns_ticket — the ownership check itself)
- data/employees.json (EMP001, EMP002 records)
- data/tickets.json   (TCK-1001, TCK-1002 records and their employee_id)
- docs/business_rules.md (BR01, BR02)
"""

EMPLOYEE_A_ID = "EMP001"
EMPLOYEE_A_TICKET_ID = "TCK-1001"

EMPLOYEE_B_ID = "EMP002"
EMPLOYEE_B_TICKET_ID = "TCK-1002"


def test_employee_a_retrieves_own_ticket(client, employee_a_headers):
    # Arrange: Employee A is EMP001, who owns TCK-1001 (from data/tickets.json,
    # not from anything the API returns).
    ticket_id = EMPLOYEE_A_TICKET_ID
    expected_owner_id = EMPLOYEE_A_ID

    # Act: ask the API for that ticket as Employee A.
    response = client.get(f"/tickets/{ticket_id}", headers=employee_a_headers)

    # Assert: the request succeeds, returns the ticket we asked for, and
    # that ticket's recorded owner is the employee we expected beforehand.
    assert response.status_code == 200
    body = response.json()
    assert body["ticket_id"] == ticket_id
    assert body["employee_id"] == expected_owner_id


def test_employee_b_retrieves_own_ticket(client, employee_b_headers):
    # Arrange: Employee B is EMP002, who owns TCK-1002 (from data/tickets.json,
    # not from anything the API returns).
    ticket_id = EMPLOYEE_B_TICKET_ID
    expected_owner_id = EMPLOYEE_B_ID

    # Act: ask the API for that ticket as Employee B.
    response = client.get(f"/tickets/{ticket_id}", headers=employee_b_headers)

    # Assert: the request succeeds, returns the ticket we asked for, and
    # that ticket's recorded owner is the employee we expected beforehand.
    assert response.status_code == 200
    body = response.json()
    assert body["ticket_id"] == ticket_id
    assert body["employee_id"] == expected_owner_id
