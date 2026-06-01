"""
Idempotency check: publishing the same message twice should not produce
duplicate rows (if the consumer is designed to be idempotent).

NOTE: The current consumer does NOT deduplicate — this test documents the
current behaviour (two rows) and acts as a change-detector if you later
add deduplication logic (at which point it should assert count == 1).
"""
import time
import uuid
import pytest

TOPIC = "weather-readings"
DRAIN_TIMEOUT_S = 10


def test_duplicate_message_behaviour(kafka_producer, db):
    station_id = f"dup-test-{uuid.uuid4().hex[:8]}"
    payload = {
        "station_id": station_id,
        "temperature_c": 21.0,
        "humidity_pct": 60.0,
        "timestamp": "2026-07-01T12:00:00",
    }

    kafka_producer.send(TOPIC, value=payload)
    kafka_producer.send(TOPIC, value=payload)
    kafka_producer.flush()

    # wait for consumer to drain both
    deadline = time.time() + DRAIN_TIMEOUT_S
    while time.time() < deadline:
        db.execute(
            "SELECT COUNT(*) FROM readings WHERE station_id = %s", (station_id,)
        )
        if db.fetchone()[0] >= 2:
            break
        time.sleep(0.5)

    db.execute("SELECT COUNT(*) FROM readings WHERE station_id = %s", (station_id,))
    count = db.fetchone()[0]

    # Documents current at-least-once behaviour.
    # Change to == 1 once exactly-once delivery is implemented.
    assert count == 2, (
        f"Expected 2 rows (at-least-once), got {count}. "
        "If you added deduplication, update this assertion to count == 1."
    )
