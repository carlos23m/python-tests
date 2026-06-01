# weather-pipeline-qa

A small weather-data ingest pipeline and the automated test suite around it,
focused on data-integrity testing of event-driven flows — the same class of
problem I handled in production at IntelliCentrics, now expressed in code
instead of manual verification steps.

## What's here

```
Two layers of tests
 ├── api_external/   Restful-booker — full CRUD + auth in Python (pytest + httpx)
 └── your pipeline   FastAPI → Kafka → Postgres, with real data-integrity checks
```

**Layer 1 — Restful-booker** (`tests/api_external/`)  
Status codes, payload shape, schema validation, auth/token flow, negative cases
(400 / 401 / 404, bad payloads, missing fields). Pure Python rewrite of the
Postman work I already know; nothing here needs Docker.

**Layer 2 — own pipeline** (`tests/messaging/`, `tests/api/`, `tests/performance/`)  
The part that matches the job description. A FastAPI service ingests weather
readings, publishes them to Kafka, and a consumer writes them to Postgres.
The messaging tests verify *no reading is silently lost* — the data-integrity
guarantee that matters in event-driven systems.

## Stack

| Layer | Technology |
|---|---|
| API service | FastAPI + Uvicorn |
| Message bus | Apache Kafka (via Confluent images) |
| Store | PostgreSQL 15 |
| Fake AWS | LocalStack (S3 / SQS) |
| Test runner | pytest |
| HTTP client | httpx |
| Load tests | Locust |
| CI | GitHub Actions |

## Quick start

```bash
# bring up the whole stack
docker compose up -d

# wait ~15 s for Kafka + Postgres to be ready, then
pip install -r requirements.txt

# Layer 1 — no Docker needed
pytest tests/api_external/ -v

# Layer 2 — needs Docker stack
pytest tests/unit/ tests/api/ tests/messaging/ -v

# Load test (against local app only, never a public API)
locust -f tests/performance/locustfile.py --headless -u 20 -r 2 --run-time 60s
```

## CI

Every push runs: lint (ruff) → unit → api → messaging integration → 60 s load
smoke test. See [.github/workflows/ci.yml](.github/workflows/ci.yml).

## Load test results

> Fill this in once you have numbers. One ASCII chart + p50/p95/p99 latencies
> and the max RPS your local stack sustained without errors goes a long way in
> a recruiter conversation.

## Project background

At IntelliCentrics I verified data flows manually — that a message published to
a queue eventually landed in the right database, in the right shape, with no
duplicates. This repo automates exactly that verification in Python, adds
performance baselines, and tacks on LocalStack to cover the AWS-service pieces.
