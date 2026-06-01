# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
"""
THE key data-integrity test: publish N messages, assert N rows land in Postgres.
This mirrors the manual verification work from IntelliCentrics, now automated.
"""
import time
import uuid
import pytest

TOPIC = "weather-readings"
N = 20
DRAIN_TIMEOUT_S = 15  # how long to wait for the consumer to catch up


def _count_rows(db, station_id: str) -> int:
    db.execute("SELECT COUNT(*) FROM readings WHERE station_id = %s", (station_id,))
    return db.fetchone()[0]


def test_publish_n_messages_all_persist(kafka_producer, db):
    station_id = f"loss-test-{uuid.uuid4().hex[:8]}"

    # Publish N readings for a unique station_id
    for i in range(N):
        kafka_producer.send(
            TOPIC,
            value={
                "station_id": station_id,
                "temperature_c": float(i),
                "humidity_pct": 50.0,
                "timestamp": "2026-07-01T00:00:00",
            },
        )
    kafka_producer.flush()

    # Wait for the consumer process to drain and write to Postgres
    deadline = time.time() + DRAIN_TIMEOUT_S
    while time.time() < deadline:
        if _count_rows(db, station_id) >= N:
            break
        time.sleep(0.5)

    persisted = _count_rows(db, station_id)
    assert persisted == N, (
        f"Data loss: published {N} messages but only {persisted} reached Postgres"
    )
