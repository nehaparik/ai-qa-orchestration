# Northstar Services — IT Service Desk API (Week 1 Starter)

A small, deterministic FastAPI service for Week 1 of the AI Quality
Engineering and QA Orchestration program. Northstar Services is a
fictional company; employees ask its IT service desk for VPN help.

This starter has **no LLM, no RAG, no chat UI, no database, no Docker,
and no CI workflow**. It reads plain JSON files and applies simple,
predictable business rules — the goal is a codebase a learner new to
Python test automation can read end to end and reason about with
confidence, before AI features are layered on in later weeks.

## What's in here

| Path | What it is |
| --- | --- |
| `app/main.py` | FastAPI routes (HTTP layer only) |
| `app/data.py` | Functions that read the JSON files in `data/` |
| `app/rules.py` | Business-rule functions (ownership checks, lookups) |
| `data/employees.json` | 4 synthetic employees |
| `data/tickets.json` | 6 synthetic VPN tickets |
| `data/service_status.json` | Current synthetic VPN status |
| `schemas/ticket.schema.json` | JSON Schema a ticket must satisfy |
| `schemas/employee_profile.schema.json`, `schemas/service_status.schema.json`, `schemas/error_response.schema.json` | JSON Schemas added in Day 2 (employee profile, VPN status, generic error body) |
| `tests/` | Baseline Day 1 pytest suite (`TestClient`, no network calls) |
| `tests/day2/` | Day 2 lesson tests: fixtures, parameterization, ownership fault injection, schema validation, Week 1 coverage gap-fill |
| `docs/business_rules.md` | BR01–BR04, in plain language |
| `docs/week1-learning-log.md` | Template for your own daily notes |
| `docs/day2-instructor-map.md` | Day 2 lesson-by-lesson implementation and verification log |
| `docs/week01-api-case-matrix.md` | Full Week 1 unique-API-scenario matrix |
| `docs/day2-run-evidence.md` | Sanitised Day 2 submission evidence (results, coverage, limitations) |
| `reports/` (git-ignored, not committed) | Local HTML/JSON test run reports generated on demand |

## Prerequisites

- Python 3.11 (the project pins `>=3.11,<3.13`)
- No API keys or accounts needed — everything here is local and synthetic

## ⚠️ Activate the virtual environment in every new terminal

This project keeps its dependencies in a local virtual environment at
`.venv/`. **Every dependency (FastAPI, pytest, etc.) is installed only
inside `.venv/`, never globally.** Each time you open a *new* terminal
(including a new VS Code integrated terminal tab), you must activate it
again before running any project command:

- macOS/Linux: `source .venv/bin/activate`
- Windows PowerShell: `.venv\Scripts\Activate.ps1`

Your prompt should then show a `(.venv)` prefix. If you skip this step,
commands like `pytest` may silently run a *different*, unrelated Python
installation on your machine that does not have this project's packages
— see [Troubleshooting](#troubleshooting) below if that happens.

Also prefer `python -m pytest -v` over a bare `pytest -v`. Running
pytest as a module of the currently active `python` is more reliable
than relying on a `pytest` command found elsewhere on your system PATH.

## Setup — macOS / Linux (bash/zsh)

```bash
# From the project root
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Setup — Windows (PowerShell)

```powershell
# From the project root
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If PowerShell blocks the activation script, run PowerShell as your normal
user and execute:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

then re-run the activation command above.

## Running the API locally

macOS/Linux:

```bash
uvicorn app.main:app --reload --port 8000
```

Windows PowerShell:

```powershell
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://127.0.0.1:8000`. Interactive docs (Swagger UI)
are at `http://127.0.0.1:8000/docs`.

**Note:** none of the automated tests (Day 1 or Day 2) need this server
running — they call the app in-process through FastAPI's `TestClient`
(see `tests/conftest.py`). Starting the API manually is only needed for
the curl examples below or for exploring `/docs` in a browser.

## Calling the endpoints with curl

All employee- and ticket-scoped endpoints require the demo header
`X-Demo-Employee-ID`. Valid demo IDs are `EMP001`, `EMP002`, `EMP003`,
`EMP004` (see `data/employees.json`).

These curl commands work the same way on macOS/Linux and in Windows
PowerShell (Windows 10+ ships `curl.exe`).

**Health check:**

```bash
curl http://127.0.0.1:8000/health
```

**Your employee profile:**

```bash
curl -H "X-Demo-Employee-ID: EMP001" http://127.0.0.1:8000/employees/me
```

**VPN service status:**

```bash
curl http://127.0.0.1:8000/services/vpn/status
```

**Get your own ticket (expect 200):**

```bash
curl -i -H "X-Demo-Employee-ID: EMP001" http://127.0.0.1:8000/tickets/TCK-1001
```

**Try to get someone else's ticket (expect 403):**

```bash
curl -i -H "X-Demo-Employee-ID: EMP002" http://127.0.0.1:8000/tickets/TCK-1001
```

**Request a ticket that doesn't exist (expect 404):**

```bash
curl -i -H "X-Demo-Employee-ID: EMP001" http://127.0.0.1:8000/tickets/TCK-9999
```

**Omit the demo header (expect 400):**

```bash
curl -i http://127.0.0.1:8000/employees/me
```

## Running the tests

All commands below are identical on macOS/Linux and Windows PowerShell
— activate the virtual environment first, then run them as shown.

### Day 1 only

```bash
python -m pytest tests/test_employees.py tests/test_tickets.py tests/test_service_status.py -v
```

Runs only the 6 original Day 1 tests, by explicit file path — one test
per endpoint plus a dedicated ticket-ownership test. This is the
canonical Day 1 regression check; see
[`docs/day2-instructor-map.md`](docs/day2-instructor-map.md) for its
recorded baseline result.

### Day 2 only

```bash
python -m pytest tests/day2/ -v
```

Runs every Day 2 lesson file (`test_01_fixtures.py` through
`test_05_week1_coverage.py`).

### Full suite (Day 1 + Day 2)

```bash
python -m pytest tests/ -v
```

As of Day 2, this collects 31 tests. See
[`docs/day2-run-evidence.md`](docs/day2-run-evidence.md) for the
verified result.

### Fault demonstrations (TEST-ONLY, disabled by default)

Some Day 2 tests can be run with one business rule deliberately broken,
to prove the test would actually catch a real regression rather than
only ever passing. This is controlled by a single pytest option,
`--day2-fault`, registered in `tests/day2/conftest.py`. **It defaults to
doing nothing** — omit it (as every command above does) and nothing
changes, in the tests or in the running application.

| `--day2-fault` value | What it breaks | Command | Expected result |
| --- | --- | --- | --- |
| `ownership` | BR02 ticket-ownership check | `python -m pytest tests/day2/test_03_ownership.py -v --day2-fault=ownership` | 2 tests **FAIL** (expected 403, got 200) |
| `missing-status` | VPN status response loses its `status` field | `python -m pytest tests/day2/test_04_schema.py -v --day2-fault=missing-status` | 1 test **FAILS** (`'status' is a required property`) |
| `wrong-status-type` | VPN status response's `status` becomes a number | `python -m pytest tests/day2/test_04_schema.py -v --day2-fault=wrong-status-type` | 1 test **FAILS** (`123 is not of type 'string'`) |

These failures are genuine assertion failures (none are marked
`xfail`) — failing is the whole point of running them. Always re-run the
same file *without* the flag afterward to confirm nothing leaked:

```bash
python -m pytest tests/day2/test_03_ownership.py -v
python -m pytest tests/day2/test_04_schema.py -v
```

Full step-by-step verification (baseline → fault → baseline again) for
each fault is recorded in
[`docs/day2-instructor-map.md`](docs/day2-instructor-map.md).

### Generating a report

`pytest-html` and `pytest-json-report` are installed via the `dev`
extras (see Setup above). Reports are written under `reports/`, which is
git-ignored on purpose — these are local run evidence for your own use,
never committed.

```bash
mkdir -p reports/day2
python -m pytest tests/ -v --html=reports/day2/baseline.html --self-contained-html --json-report --json-report-file=reports/day2/baseline.json
```

The same flags work on any of the commands above, e.g. to capture a
fault demonstration's own report:

```bash
python -m pytest tests/day2/test_03_ownership.py -v --day2-fault=ownership --html=reports/day2/ownership-fault.html --self-contained-html --json-report --json-report-file=reports/day2/ownership-fault.json
```

**Before sharing a report with anyone**, remember the HTML/JSON files
under `reports/` are generated locally and are not reviewed for
sensitive content automatically — see
[`docs/day2-run-evidence.md`](docs/day2-run-evidence.md) for what was
checked in this project's own reports and why they stay out of Git.

## Business rules

See [`docs/business_rules.md`](docs/business_rules.md) for BR01–BR04 and
where each one is implemented in the code.

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'" when running pytest

This means the terminal is not using this project's `.venv`. It is
almost always because a *new* terminal was opened and `.venv` was never
activated in it, so `pytest` (or `python`) fell back to some other
Python installation on your machine that doesn't have this project's
packages installed.

**macOS/Linux — run these one at a time and read the output of each:**

```bash
source .venv/bin/activate
python -m pip show fastapi
python -m pytest -v
```

- `source .venv/bin/activate` must succeed silently and your prompt
  should now start with `(.venv)`.
- `python -m pip show fastapi` should print a `Name: fastapi` block. If
  it instead prints `WARNING: Package(s) not found: fastapi`, the
  environment you activated is not the one the project was installed
  into (or the install step was never run in it).
- If FastAPI is missing inside the activated `.venv`, install the
  project's dependencies into it:

  ```bash
  python -m pip install -e ".[dev]"
  ```

  Then re-run `python -m pytest -v`.

**Windows PowerShell — the same steps:**

```powershell
.venv\Scripts\Activate.ps1
python -m pip show fastapi
python -m pytest -v
```

If FastAPI is missing:

```powershell
python -m pip install -e ".[dev]"
```

### A second, unrelated virtual environment folder

If you (or an editor) ever created a second environment folder, such as
a plain `venv/` alongside `.venv/`, make sure you always activate
`.venv/` specifically. Two environments with similar names is a common
source of this exact error — when in doubt, run `python -m pip show
fastapi` after activating to confirm you're in the right one.
