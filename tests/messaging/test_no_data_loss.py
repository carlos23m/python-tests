# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
"""
THE key data-integrity test: publish N messages, assert N rows land in Postgres.
"""
import os
import uuid

TOPIC = os.getenv("KAFKA_TOPIC", "weather-readings")
N = 20
DRAIN_TIMEOUT_S = 15


def _count_rows(db, station_id: str) -> int:
    """Return the number of persisted rows for a given station_id."""
    db.execute("SELECT COUNT(*) FROM readings WHERE station_id = %s", (station_id,))
    return db.fetchone()[0]


def test_publish_n_messages_all_persist(kafka_producer, db, wait_for_rows):
    """Publish N messages and assert exactly N rows land in Postgres — no silent drops."""
    # uuid suffix isolates this run's rows so a leftover table from a prior run can't inflate the count
    station_id = f"loss-test-{uuid.uuid4().hex[:8]}"

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
    # flush() blocks until all messages are handed to the broker; without it the loop
    # could return before all N messages are actually in Kafka
    kafka_producer.flush()

    wait_for_rows(station_id, N, timeout=DRAIN_TIMEOUT_S)

    persisted = _count_rows(db, station_id)
    assert persisted == N, (
        f"Data loss: published {N} messages but only {persisted} reached Postgres"
    )
