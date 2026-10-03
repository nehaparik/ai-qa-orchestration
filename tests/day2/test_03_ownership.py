"""
Day 2, Lesson 3: Ownership fault injection.

Where BR02 ("an employee cannot view another employee's ticket") is
actually enforced:

- `app/rules.py`: `employee_owns_ticket(ticket, employee_id)` is the one
  function that decides ownership -- it compares `ticket["employee_id"]`
  to the requester's id and returns True/False.
- `app/main.py`: the `GET /tickets/{ticket_id}` route (`get_ticket`) calls
  `rules.employee_owns_ticket(...)` directly, as a plain function call.
  This is different from how the route gets the *current employee*
  (`get_current_employee`), which is wired in through FastAPI's
  `Depends(...)` and could be swapped out per-request using
  `app.dependency_overrides`. The ownership check has no such seam --
  it's just a function call inside the route body.

Why this file injects the fault with `monkeypatch` instead of building a
second, isolated FastAPI app instance:
Because there is no `Depends(...)` seam for the ownership check, there is
nothing in this architecture equivalent to `dependency_overrides` for it.
The safe substitute is to monkeypatch the exact function the route calls
(`app.rules.employee_owns_ticket`) using pytest's built-in `monkeypatch`
fixture. `monkeypatch` guarantees the original function is put back
automatically the moment a test ends, pass or fail -- so the fault never
leaks into another test, never touches the app when run outside pytest,
never changes `get_current_employee` (authentication is untouched), and
never changes any file in `data/` (no persistent data is touched).

How to use the fault, and what each run proves:

1. Normal run (fault NOT injected) -- shows ownership enforcement is real:

     python -m pytest tests/day2/test_03_ownership.py -v

   Expected: both tests below PASS (403, no foreign ticket data leaked).

2. Fault-injected run -- proves the two tests below are not vacuous, i.e.
   they would actually catch it if BR02 broke. The test code is NOT
   changed between this run and the one above:

     python -m pytest tests/day2/test_03_ownership.py -v --day2-fault=ownership

   Expected: both tests FAIL. With ownership bypassed, the route now
   returns 200 and the *other* employee's real ticket, so the first
   assertion (`status_code == 403`) fails for real. This is a genuine
   failure, not something marked `xfail` -- an honest assertion error is
   exactly what demonstrates these tests would catch a real regression.

3. Normal run again -- proves the fault does not leak between runs:

     python -m pytest tests/day2/test_03_ownership.py -v

   Expected: PASS again, identical to step 1.

`--day2-fault` is registered in `tests/day2/conftest.py`. It only affects
a test that explicitly requests the `ownership_fault` fixture below, so
it has no effect on `test_01_fixtures.py`, `test_02_parameterized.py`, the
Day 1 suite, or the application when run normally outside pytest.
"""

import pytest

from app import rules

EMPLOYEE_A_ID = "EMP001"
EMPLOYEE_A_TICKET_ID = "TCK-1001"
EMPLOYEE_A_TICKET_SUBJECT = "VPN client fails to connect from home network"

EMPLOYEE_B_ID = "EMP002"
EMPLOYEE_B_TICKET_ID = "TCK-1002"
EMPLOYEE_B_TICKET_SUBJECT = "VPN password reset needed"

DOCUMENTED_DENIAL_MESSAGE = "You may not view another employee's ticket."


@pytest.fixture()
def ownership_fault(request, monkeypatch):
    """Bypass BR02 ownership enforcement, but only when explicitly asked for.

    Reads the `--day2-fault` command-line option. If it is anything other
    than "ownership" (including the default, unset), this fixture does
    nothing -- the real `app.rules.employee_owns_ticket` keeps running,
    completely unmodified.

    If it *is* "ownership", this fixture replaces
    `app.rules.employee_owns_ticket` with a fake version that always
    returns True ("yes, this employee owns this ticket", no matter whose
    ticket it actually is). That one function is BR02's entire ownership
    decision, so faking it simulates BR02 being broken.

    `monkeypatch` is pytest's built-in fixture for exactly this kind of
    swap: it remembers the original function and restores it the instant
    this test ends, whether the test passed or failed. Nothing here
    survives past the single test that used it, and no other test file
    is affected.
    """
    fault = request.config.getoption("--day2-fault")
    if fault == "ownership":
        monkeypatch.setattr(
            rules, "employee_owns_ticket", lambda ticket, employee_id: True
        )
    return fault


def test_employee_a_cannot_view_employee_bs_ticket(
    client, employee_a_headers, ownership_fault
):
    # Arrange: TCK-1002 belongs to Employee B (EMP002), not Employee A,
    # per data/tickets.json.
    ticket_id = EMPLOYEE_B_TICKET_ID

    # Act: exercise the real endpoint, exactly as a client would.
    response = client.get(f"/tickets/{ticket_id}", headers=employee_a_headers)

    # Assert: BR02 must deny this with exactly the documented 403 message,
    # and must not leak any of Employee B's actual ticket content.
    assert response.status_code == 403
    assert response.json() == {"detail": DOCUMENTED_DENIAL_MESSAGE}
    assert EMPLOYEE_B_TICKET_SUBJECT not in response.text
    assert "employee_id" not in response.json()


def test_employee_b_cannot_view_employee_as_ticket(
    client, employee_b_headers, ownership_fault
):
    # Arrange: TCK-1001 belongs to Employee A (EMP001), not Employee B,
    # per data/tickets.json.
    ticket_id = EMPLOYEE_A_TICKET_ID

    # Act: exercise the real endpoint, exactly as a client would.
    response = client.get(f"/tickets/{ticket_id}", headers=employee_b_headers)

    # Assert: BR02 must deny this with exactly the documented 403 message,
    # and must not leak any of Employee A's actual ticket content.
    assert response.status_code == 403
    assert response.json() == {"detail": DOCUMENTED_DENIAL_MESSAGE}
    assert EMPLOYEE_A_TICKET_SUBJECT not in response.text
    assert "employee_id" not in response.json()
