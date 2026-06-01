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
    with httpx.Client(base_url=base_url, timeout=10) as c:
        yield c


# ── Health ─────────────────────────────────────────────────────────────────────

def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ── Ingest ─────────────────────────────────────────────────────────────────────

def test_ingest_valid_reading_returns_202(client):
    resp = client.post("/readings", json=VALID_READING)
    assert resp.status_code == 202


def test_ingest_response_contains_station_id(client):
    resp = client.post("/readings", json=VALID_READING)
    assert resp.json()["station_id"] == VALID_READING["station_id"]


def test_ingest_missing_station_id_returns_422(client):
    resp = client.post("/readings", json={"temperature_c": 10.0, "humidity_pct": 50})
    assert resp.status_code == 422


def test_ingest_humidity_out_of_range_returns_422(client):
    bad = {**VALID_READING, "humidity_pct": 150}
    resp = client.post("/readings", json=bad)
    assert resp.status_code == 422


def test_ingest_empty_body_returns_422(client):
    resp = client.post("/readings", json={})
    assert resp.status_code == 422


def test_ingest_extra_fields_are_ignored(client):
    payload = {**VALID_READING, "unknown_field": "surprise"}
    resp = client.post("/readings", json=payload)
    assert resp.status_code == 202


# ── Query ──────────────────────────────────────────────────────────────────────

def test_get_readings_returns_200(client):
    resp = client.get("/readings/TEST-001")
    assert resp.status_code == 200
    body = resp.json()
    assert "readings" in body
    assert isinstance(body["readings"], list)


def test_get_readings_schema(client):
    # TODO: assert each item in readings has id, station_id, temperature_c,
    # humidity_pct, timestamp keys
    ...
