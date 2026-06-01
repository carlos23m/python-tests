"""
End-to-end pipeline test: POST one reading to the API, assert it eventually
appears in Postgres. Covers the full path: HTTP → Kafka → consumer → DB.
"""
import time
import uuid
import pytest
import httpx

DRAIN_TIMEOUT_S = 20


def test_one_reading_flows_through_full_pipeline(base_url, db):
    station_id = f"e2e-{uuid.uuid4().hex[:8]}"
    payload = {
        "station_id": station_id,
        "temperature_c": 19.5,
        "humidity_pct": 72.0,
    }

    # Step 1: ingest via the HTTP API
    resp = httpx.post(f"{base_url}/readings", json=payload, timeout=10)
    assert resp.status_code == 202, f"Unexpected status: {resp.status_code} {resp.text}"

    # Step 2: wait for consumer to write to Postgres
    deadline = time.time() + DRAIN_TIMEOUT_S
    while time.time() < deadline:
        db.execute(
            "SELECT COUNT(*) FROM readings WHERE station_id = %s", (station_id,)
        )
        if db.fetchone()[0] >= 1:
            break
        time.sleep(0.5)

    # Step 3: assert persistence
    db.execute(
        "SELECT temperature_c, humidity_pct FROM readings WHERE station_id = %s",
        (station_id,),
    )
    row = db.fetchone()
    assert row is not None, f"Reading for station {station_id} never reached Postgres"
    assert row[0] == pytest.approx(19.5)
    assert row[1] == pytest.approx(72.0)


def test_multiple_readings_same_station_all_persisted(base_url, db):
    # TODO: POST 5 readings for the same station_id, assert all 5 land in DB
    ...


def test_query_endpoint_reflects_persisted_data(base_url, db):
    # TODO: POST a reading, wait for persistence, then GET /readings/{station_id}
    # and assert the HTTP response contains the reading you posted
    ...
