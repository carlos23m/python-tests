"""
Verify that messages published in sequence are persisted in the same order
(ascending by the sequence number embedded in temperature_c).
"""
import time
import uuid
import pytest

TOPIC = "weather-readings"
N = 10
DRAIN_TIMEOUT_S = 15


def test_messages_persisted_in_published_order(kafka_producer, db):
    station_id = f"order-test-{uuid.uuid4().hex[:8]}"

    for seq in range(N):
        kafka_producer.send(
            TOPIC,
            value={
                "station_id": station_id,
                "temperature_c": float(seq),   # seq number encoded as temp
                "humidity_pct": 50.0,
                "timestamp": "2026-07-01T00:00:00",
            },
        )
    kafka_producer.flush()

    deadline = time.time() + DRAIN_TIMEOUT_S
    while time.time() < deadline:
        db.execute(
            "SELECT COUNT(*) FROM readings WHERE station_id = %s", (station_id,)
        )
        if db.fetchone()[0] >= N:
            break
        time.sleep(0.5)

    # TODO: query the rows ordered by id (insertion order) and assert
    # that temperature_c values are 0.0, 1.0, 2.0, ... N-1 in that order
    ...
