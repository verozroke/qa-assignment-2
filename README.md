# QA Assignment 2 — Automation, Quality Gates & Metrics

Extends Assignment 1 with quality gate enforcement, mock server for CI, HTML reporting, and metrics collection.

## What Changed From Assignment 1

- **Mock server** (`mock_server.py`) — simulates the ticket management app so tests run in CI without external dependencies
- **Quality gates** (`quality_gate.py`) — enforces pass rate, failure count, and skip thresholds after each test run
- **HTML reporting** — pytest-html generates self-contained reports uploaded as CI artifacts
- **Strict CI mode** — `SKIP_ON_UNREACHABLE=false` since the mock server guarantees availability

## Repository Structure

```
├── .github/workflows/qa-automation.yml   # CI/CD pipeline with mock server
├── config/
│   └── settings.py
├── tests/
│   ├── conftest.py
│   ├── api/
│   │   └── test_api_endpoints.py
│   └── ui/
│       ├── conftest.py
│       ├── test_login.py
│       ├── test_logout.py
│       └── test_create_ticket_flow.py
├── utils/
│   ├── api_client.py
│   ├── base_test.py
│   ├── logger.py
│   └── ui_pages.py
├── mock_server.py               # Simulates API + UI of the ticket system
├── quality_gate.py              # Parses JUnit XML and enforces thresholds
├── .env.example
├── pytest.ini
└── requirements.txt
```

## Tools

| Tool           | Purpose                     |
| -------------- | --------------------------- |
| Pytest         | Test framework              |
| pytest-html    | HTML report generation      |
| Playwright     | UI automation               |
| Requests       | API testing                 |
| GitHub Actions | CI/CD pipeline              |
| Mock server    | Local app simulation for CI |

## Setup

### Installation

```bash
git clone https://github.com/almiinho/QA-Assignment-1.git
cd QA-Assignment-1
pip install -r requirements.txt
playwright install --with-deps chromium
```

### Running Locally

Start the mock server, then run tests:

```bash
# Terminal 1: start mock server
python mock_server.py

# Terminal 2: run tests
pytest --junitxml=test-results/pytest-report.xml --html=test-results/report.html --self-contained-html

# Check quality gate
python quality_gate.py
```

## Mock Server

`mock_server.py` runs on `http://localhost:8080` and simulates:

| Endpoint            | Method   | Behavior                                                |
| ------------------- | -------- | ------------------------------------------------------- |
| `/api/auth/login`   | POST     | Returns token for valid credentials, 401 otherwise      |
| `/api/tickets`      | POST     | Creates ticket, returns 422 for missing fields          |
| `/api/tickets/{id}` | GET      | Returns ticket by ID                                    |
| `/login`            | GET/POST | Login page with form, redirects to dashboard on success |
| `/dashboard`        | GET      | Dashboard with create ticket link and logout button     |
| `/tickets/new`      | GET/POST | Ticket creation form with success message               |
| `/logout`           | GET      | Redirects to login page                                 |

## Quality Gates

`quality_gate.py` runs after tests and enforces:

| Criteria                  | Threshold |
| ------------------------- | --------- |
| Minimum pass rate         | 80%       |
| Maximum critical failures | 0         |
| Maximum skipped tests     | 50%       |

Example output:

```
============================================================
QUALITY GATE REPORT
============================================================
  Total tests:    8
  Passed:         8
  Failed:         0
  Skipped:        0
  Pass rate:      100.0%
  Skipped rate:   0.0%
  Execution time: 32.70s
============================================================

QUALITY GATE: PASSED
```

If any threshold is violated, the script exits with code 1 and the CI pipeline fails.

## CI/CD Pipeline

```
Checkout → Python setup → Install deps → Playwright install → Start mock server → Run tests → Quality gate → Upload artifacts
```

Key configuration:

- Mock server starts as a background process before tests
- `|| true` after pytest ensures full report is generated even if tests fail
- Quality gate evaluates results as a separate step
- HTML report and JUnit XML are always uploaded as artifacts

## Test Suite & Results

| #   | Test                                 | Type | Result |
| --- | ------------------------------------ | ---- | ------ |
| 1   | test_authentication_endpoint         | API  | Passed |
| 2   | test_create_ticket_endpoint          | API  | Passed |
| 3   | test_get_ticket_endpoint             | API  | Passed |
| 4   | test_create_ticket_with_invalid_data | API  | Passed |
| 5   | test_login_with_valid_credentials    | UI   | Passed |
| 6   | test_login_with_invalid_credentials  | UI   | Passed |
| 7   | test_create_ticket_flow              | UI   | Passed |
| 8   | test_logout                          | UI   | Passed |

## Metrics

| Metric                   | Value        |
| ------------------------ | ------------ |
| Total tests              | 8            |
| Pass rate                | 100%         |
| API tests                | 4            |
| UI tests                 | 4            |
| Execution time           | ~33 seconds  |
| Pipeline time            | ~2-3 minutes |
| Critical module coverage | 100%         |
| High module coverage     | 100%         |

## Defects Found During Development

| Issue                                            | Resolution                                |
| ------------------------------------------------ | ----------------------------------------- |
| Empty base URL in CI caused MissingSchema errors | Added fallback defaults in workflow       |
| URL-encoded form data not decoded by mock server | Replaced manual parsing with `parse_qs()` |
| All tests skipped when app unreachable           | Added mock server to CI pipeline          |

## Course

Advanced Quality Assurance — Assignment 2 (Week 4)
