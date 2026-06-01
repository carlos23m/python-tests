# weather-pipeline-qa

A weather-data ingest pipeline with an automated test suite focused on
data-integrity verification of event-driven flows — the same class of problem
I handled in production at IntelliCentrics, now expressed in code instead of
manual verification steps.

## Architecture

```
HTTP client
    │
    ▼
FastAPI  ──POST /readings──▶  Kafka (weather-readings topic)
    │                                    │
GET /readings/{id}              consumer process
    │                                    │
    └──────────────── Postgres ◀─────────┘
                     (readings table)

LocalStack: S3 + SQS smoke-tested independently
```

## Test suite — 54 tests across 4 layers

### Layer 1 · External API (`tests/api_external/`) — 21 tests, no Docker needed

Tests against the public [Restful-booker](https://restful-booker.herokuapp.com) API.

| File | What it covers |
|---|---|
| `test_auth.py` | Token acquisition, wrong credentials, missing fields |
| `test_booking_crud.py` | Full CRUD cycle — create, read, PUT, PATCH, delete + 404 verification |
| `test_negative.py` | Missing fields, invalid dates, wrong IDs, unauthenticated mutations, garbage tokens |

### Layer 2 · Own pipeline (`tests/unit/`, `tests/api/`, `tests/messaging/`) — 29 tests

**Unit** (`tests/unit/`) — 8 tests, pure Python, no infrastructure  
Pydantic model validation: boundaries (humidity 0–100), type coercion, required fields.

**API** (`tests/api/`) — 10 tests, needs app + Kafka + Postgres  
FastAPI endpoint contract: status codes, response shape, field schema, `limit` parameter.

**Messaging** (`tests/messaging/`) — 11 tests, needs full stack

| File | What it verifies |
|---|---|
| `test_pipeline_e2e.py` | Full path: HTTP → Kafka → consumer → Postgres |
| `test_no_data_loss.py` | Publish 20 messages → exactly 20 rows in Postgres |
| `test_ordering.py` | Messages land in publish order (single partition) |
| `test_duplicates.py` | At-least-once behaviour documented; change detector for future deduplication |
| `test_malformed.py` | Consumer survives 6 poison-message shapes without crashing; range-validation gap documented |

### Layer 3 · AWS / LocalStack (`tests/aws/`) — 2 tests

S3 put/get and SQS send/receive against a local LocalStack container.

### Load test (`tests/performance/`)

Locust script: 5× POST `/readings`, 2× GET `/readings/{id}`, 1× GET `/health`.  
Run with `--exit-code-on-error 1` in CI so a >5% error rate fails the build.

## Stack

| Component | Technology |
|---|---|
| API service | FastAPI + Uvicorn |
| Message bus | Apache Kafka (Confluent 7.6) |
| Database | PostgreSQL 15 |
| Fake AWS | LocalStack 3.4 (S3, SQS, SNS) |
| ORM | SQLAlchemy 2 |
| Test runner | pytest 8 + pytest-asyncio |
| HTTP client | httpx |
| Load tests | Locust |
| Lint | ruff |
| CI | GitHub Actions |

## Quick start

```bash
# 1. Start infrastructure
docker compose up -d postgres zookeeper kafka localstack

# 2. Wait for services to be healthy (~20 s), then start the app
docker compose up -d app consumer

# 3. Install test dependencies
pip install -r requirements.txt

# 4. Run each layer
pytest tests/api_external/ -v                     # no Docker needed
pytest tests/unit/ -v                             # no Docker needed
pytest tests/api/ tests/messaging/ tests/aws/ -v  # needs full stack
```

**Environment variables** (all have defaults matching docker-compose.yml):

| Variable | Default |
|---|---|
| `APP_BASE_URL` | `http://localhost:8000` |
| `DATABASE_URL` | `postgresql://weather:weather@localhost:5432/weather` |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` |
| `KAFKA_TOPIC` | `weather-readings` |

## CI

Every push runs in order:

1. **Lint** — `ruff check .`
2. **External API tests** — no infrastructure needed
3. **Start infra** — Postgres, Zookeeper, Kafka, LocalStack via Docker Compose; health-checked before proceeding
4. **Start app + consumer** — waited on via `GET /health` poll
5. **Unit → API → Messaging → AWS** — each layer in sequence
6. **Load smoke** — 60 s Locust run, fails build on >5% error rate

See [.github/workflows/ci.yml](.github/workflows/ci.yml).

## Notable design decisions

**Dual Kafka listeners** — `docker-compose.yml` configures two listeners:
`PLAINTEXT://localhost:9092` for host-side test runners and `PLAINTEXT_INTERNAL://kafka:29092`
for the app/consumer containers. A single `localhost:9092` advertised listener causes
containers to resolve the broker address to themselves.

**Consumer poison-message handling** — the `value_deserializer` in `KafkaConsumer` runs
before the loop body, so a `JSONDecodeError` there bypasses any `try/except` inside the
loop and crashes the process. JSON parsing is done manually inside the guard instead.

**Polling pattern** — messaging tests use a shared `wait_for_rows` fixture (in `conftest.py`)
rather than inline `time.sleep` loops. One place to tune the timeout; one consistent
failure message.

---

Designed and created by Carlos Mendez · [linkedin.com/in/carlos-mendez1](https://www.linkedin.com/in/carlos-mendez1) · 2026
