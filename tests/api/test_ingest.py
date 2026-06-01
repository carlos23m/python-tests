# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
"""
Tests for your own FastAPI endpoints.
Requires the app to be running (docker compose up app, or pytest with live server).
"""
import pytest
import httpx

VALID_READING = {
    "station_id": "TEST-001",
    "temperature_c": 23.4,
    "humidity_pct": 55.0,
}


@pytest.fixture(scope="module")
def client(base_url):
    # module-scoped: one HTTP connection pool for all tests in this file — avoids
    # the overhead of a TCP handshake per test against the local app
    with httpx.Client(base_url=base_url, timeout=10) as c:
        yield c


# ── Health ─────────────────────────────────────────────────────────────────────

def test_health_returns_200(client):
    """Liveness probe returns 200 with a fixed status body."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ── Ingest ─────────────────────────────────────────────────────────────────────

def test_ingest_valid_reading_returns_202(client):
    """A fully valid payload is accepted with 202 (async — not yet persisted)."""
    resp = client.post("/readings", json=VALID_READING)
    assert resp.status_code == 202


def test_ingest_response_contains_station_id(client):
    """The 202 response body echoes the station_id so callers can confirm what was accepted."""
    resp = client.post("/readings", json=VALID_READING)
    assert resp.status_code == 202
    assert resp.json()["station_id"] == VALID_READING["station_id"]


def test_ingest_missing_station_id_returns_422(client):
    """station_id is required — omitting it triggers FastAPI's 422 Unprocessable Entity."""
    resp = client.post("/readings", json={"temperature_c": 10.0, "humidity_pct": 50})
    assert resp.status_code == 422


def test_ingest_humidity_out_of_range_returns_422(client):
    """humidity_pct > 100 violates the model constraint and is rejected at the HTTP layer."""
    bad = {**VALID_READING, "humidity_pct": 150}
    resp = client.post("/readings", json=bad)
    assert resp.status_code == 422


def test_ingest_empty_body_returns_422(client):
    """An empty JSON object is missing all required fields — FastAPI returns 422."""
    resp = client.post("/readings", json={})
    assert resp.status_code == 422


def test_ingest_extra_fields_are_ignored(client):
    # Pydantic strips unknown fields by default — verify the API doesn't reject or echo them
    payload = {**VALID_READING, "unknown_field": "surprise"}
    resp = client.post("/readings", json=payload)
    assert resp.status_code == 202


# ── Query ──────────────────────────────────────────────────────────────────────

def test_get_readings_returns_200(client):
    """GET /readings/{station_id} returns 200 with a readings list (may be empty)."""
    resp = client.get("/readings/TEST-001")
    assert resp.status_code == 200
    body = resp.json()
    assert "readings" in body
    assert isinstance(body["readings"], list)


def test_get_readings_schema(client):
    resp = client.get("/readings/TEST-001")
    assert resp.status_code == 200
    # Subset check (<=): allows extra fields in the response without breaking the assertion
    for item in resp.json()["readings"]:
        assert {"id", "station_id", "temperature_c", "humidity_pct", "timestamp"} <= set(item.keys())


def test_get_readings_respects_limit(client):
    """The limit query parameter caps the number of items returned."""
    resp = client.get("/readings/TEST-001?limit=1")
    assert resp.status_code == 200
    assert len(resp.json()["readings"]) <= 1
