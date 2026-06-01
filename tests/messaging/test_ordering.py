# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
"""
Verify that messages published in sequence are persisted in the same order
(ascending by the sequence number embedded in temperature_c).
"""
import os
import uuid

TOPIC = os.getenv("KAFKA_TOPIC", "weather-readings")
N = 10
DRAIN_TIMEOUT_S = 15


def test_messages_persisted_in_published_order(kafka_producer, db, wait_for_rows):
    station_id = f"order-test-{uuid.uuid4().hex[:8]}"

    for seq in range(N):
        kafka_producer.send(
            TOPIC,
            value={
                "station_id": station_id,
                "temperature_c": float(seq),
                "humidity_pct": 50.0,
                "timestamp": "2026-07-01T00:00:00",
            },
        )
    kafka_producer.flush()

    wait_for_rows(station_id, N, timeout=DRAIN_TIMEOUT_S)

    db.execute(
        "SELECT temperature_c FROM readings WHERE station_id = %s ORDER BY id ASC",
        (station_id,),
    )
    rows = db.fetchall()
    assert len(rows) == N, f"Expected {N} rows, got {len(rows)}"
    assert [r[0] for r in rows] == [float(seq) for seq in range(N)], (
        "Rows are not in published order"
    )
