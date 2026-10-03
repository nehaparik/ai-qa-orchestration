"""
Shared fixtures for Day 2 tests.

pytest automatically finds `conftest.py` files in parent folders too, so
every fixture in `tests/conftest.py` (like `client`) is already available
here without importing anything. This file only adds fixtures that Day 1
did not need yet.

BR01 (see docs/business_rules.md) says the "current employee" for a
request comes from the `X-Demo-Employee-ID` header. Instead of typing
that header name as a plain string in every test, we import the same
`DEMO_HEADER_NAME` constant the app itself uses (`app/main.py`). That way
these tests reuse the app's own authentication mechanism rather than
re-inventing it, and would still work if the header name ever changed.
"""

import json
from pathlib import Path

import jsonschema
import pytest

from app.main import DEMO_HEADER_NAME

SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"


def pytest_addoption(parser):
    """Register a TEST-ONLY pytest option used by test_03_ownership.py and
    test_04_schema.py.

    `pytest_addoption` must live in a conftest.py (pytest reads it before
    normal test collection), which is why it is here rather than in the
    test files themselves. Registering the option does nothing by itself
    -- it has no effect unless a test explicitly reads it via
    `request.config.getoption("--day2-fault")`, which only the fault
    fixtures in those two files do. It has no effect on
    test_01_fixtures.py, test_02_parameterized.py, the Day 1 suite, or the
    application when run normally outside pytest.
    """
    parser.addoption(
        "--day2-fault",
        action="store",
        default=None,
        choices=["ownership", "missing-status", "wrong-status-type"],
        help=(
            "TEST-ONLY: inject a named fault to prove a test would "
            "actually catch a real regression, instead of only ever "
            "passing. 'ownership' (test_03_ownership.py) bypasses the "
            "BR02 ownership check. 'missing-status' and "
            "'wrong-status-type' (test_04_schema.py) corrupt the VPN "
            "service status response at its source. In every case, "
            "pytest's monkeypatch fixture restores the real behaviour "
            "automatically once the requesting test ends. Never set this "
            "for a normal test run."
        ),
    )


@pytest.fixture()
def employee_a_headers() -> dict:
    """Request headers that identify Employee A (EMP001, Dana Whitfield).

    EMP001 is a real employee_id from data/employees.json.
    """
    return {DEMO_HEADER_NAME: "EMP001"}


@pytest.fixture()
def employee_b_headers() -> dict:
    """Request headers that identify Employee B (EMP002, Marcus Lee).

    EMP002 is a real employee_id from data/employees.json.
    """
    return {DEMO_HEADER_NAME: "EMP002"}


@pytest.fixture()
def employee_c_headers() -> dict:
    """Request headers that identify Employee C (EMP003, Priya Nair).

    EMP003 is a real employee_id from data/employees.json. Added for
    tests/day2/test_05_week1_coverage.py, which exercises employees that
    earlier Day 2 lessons never touched.
    """
    return {DEMO_HEADER_NAME: "EMP003"}


@pytest.fixture()
def employee_d_headers() -> dict:
    """Request headers that identify Employee D (EMP004, Oliver Grant).

    EMP004 is a real employee_id from data/employees.json. Added for
    tests/day2/test_05_week1_coverage.py.
    """
    return {DEMO_HEADER_NAME: "EMP004"}


@pytest.fixture()
def unknown_employee_headers() -> dict:
    """Headers naming an employee id that does not exist in
    data/employees.json -- the BR01 "unknown employee" negative case.
    """
    return {DEMO_HEADER_NAME: "EMP999"}


@pytest.fixture()
def assert_matches_schema():
    """Return a reusable helper for validating a response body against one
    of the project's JSON Schema files in schemas/.

    This is a "fixture factory": rather than returning a fixed value (like
    `employee_a_headers` does), this fixture returns a function. Each test
    calls that function with its own response body and schema filename, so
    the same fixture is reused across every schema in this lesson
    (employee profile, ticket, service status, error) instead of
    duplicating the "open the file, load it, validate" steps four times.
    """

    def _assert_matches_schema(payload: dict, schema_filename: str) -> None:
        schema_path = SCHEMAS_DIR / schema_filename
        with open(schema_path, "r", encoding="utf-8") as schema_file:
            schema = json.load(schema_file)

        # Raises jsonschema.exceptions.ValidationError if payload doesn't
        # match the schema (missing required field, wrong type, etc.).
        jsonschema.validate(instance=payload, schema=schema)

    return _assert_matches_schema
