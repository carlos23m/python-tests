# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
"""
End-to-end pipeline test: POST one reading to the API, assert it eventually
appears in Postgres. Covers the full path: HTTP → Kafka → consumer → DB.
"""
import time
import uuid
import pytest
import httpx

# Budget for the async Kafka → consumer → Postgres path. The consumer runs out-of-process
# so there is no synchronous signal; we poll until the row appears or time runs out.
DRAIN_TIMEOUT_S = 20


def test_one_reading_flows_through_full_pipeline(base_url, db):
    # Unique suffix prevents collision if the DB isn't wiped between runs
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

    # Step 3: assert persistence — re-query for field values; the loop above only checked count
    db.execute(
        "SELECT temperature_c, humidity_pct FROM readings WHERE station_id = %s",
        (station_id,),
    )
    row = db.fetchone()
    assert row is not None, f"Reading for station {station_id} never reached Postgres"
    assert row[0] == pytest.approx(19.5)   # approx: float columns may not round-trip exactly
    assert row[1] == pytest.approx(72.0)


def test_multiple_readings_same_station_all_persisted(base_url, db):
    station_id = f"multi-e2e-{uuid.uuid4().hex[:8]}"
    n = 5
    for i in range(n):
        resp = httpx.post(
            f"{base_url}/readings",
            json={"station_id": station_id, "temperature_c": float(i), "humidity_pct": 50.0},
            timeout=10,
        )
        assert resp.status_code == 202

    # Wait for ALL n rows, not just the first — catches partial data-loss
    deadline = time.time() + DRAIN_TIMEOUT_S
    while time.time() < deadline:
        db.execute("SELECT COUNT(*) FROM readings WHERE station_id = %s", (station_id,))
        if db.fetchone()[0] >= n:
            break
        time.sleep(0.5)

    db.execute("SELECT COUNT(*) FROM readings WHERE station_id = %s", (station_id,))
    assert db.fetchone()[0] == n


def test_query_endpoint_reflects_persisted_data(base_url, db):
    station_id = f"get-e2e-{uuid.uuid4().hex[:8]}"
    resp = httpx.post(
        f"{base_url}/readings",
        json={"station_id": station_id, "temperature_c": 25.5, "humidity_pct": 65.0},
        timeout=10,
    )
    assert resp.status_code == 202

    # Wait before querying the GET endpoint — it reads from DB, not Kafka,
    # so it would return empty if the consumer hasn't written yet
    deadline = time.time() + DRAIN_TIMEOUT_S
    while time.time() < deadline:
        db.execute("SELECT COUNT(*) FROM readings WHERE station_id = %s", (station_id,))
        if db.fetchone()[0] >= 1:
            break
        time.sleep(0.5)

    resp = httpx.get(f"{base_url}/readings/{station_id}", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert data["station_id"] == station_id
    assert len(data["readings"]) == 1
    assert data["readings"][0]["temperature_c"] == pytest.approx(25.5)
    assert data["readings"][0]["humidity_pct"] == pytest.approx(65.0)
