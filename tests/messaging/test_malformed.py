"""
Poison-message test: a malformed message on the topic must NOT crash the consumer.
The consumer should log the error, skip the bad message, and keep processing.
"""
import json
import time
import uuid
import pytest
from kafka import KafkaProducer

TOPIC = "weather-readings"
DRAIN_TIMEOUT_S = 15


@pytest.fixture(scope="module")
def raw_producer():
    """A producer that sends raw bytes so we can craft truly malformed payloads."""
    producer = KafkaProducer(bootstrap_servers="localhost:9092")
    yield producer
    producer.close()


def _good_payload(station_id: str) -> dict:
    return {
        "station_id": station_id,
        "temperature_c": 20.0,
        "humidity_pct": 50.0,
        "timestamp": "2026-07-01T00:00:00",
    }


def test_consumer_survives_poison_message_and_processes_next(
    raw_producer, kafka_producer, db
):
    station_id_after = f"after-poison-{uuid.uuid4().hex[:8]}"

    # 1. Send a poison message (invalid JSON bytes)
    raw_producer.send(TOPIC, value=b"THIS IS NOT JSON {{{}}")
    raw_producer.flush()

    # 2. Immediately after, send a valid message
    kafka_producer.send(TOPIC, value=_good_payload(station_id_after))
    kafka_producer.flush()

    # 3. Assert the valid message still lands in Postgres
    deadline = time.time() + DRAIN_TIMEOUT_S
    while time.time() < deadline:
        db.execute(
            "SELECT COUNT(*) FROM readings WHERE station_id = %s", (station_id_after,)
        )
        if db.fetchone()[0] >= 1:
            break
        time.sleep(0.5)

    db.execute(
        "SELECT COUNT(*) FROM readings WHERE station_id = %s", (station_id_after,)
    )
    count = db.fetchone()[0]
    assert count == 1, (
        "Consumer appears to have crashed after the poison message "
        f"— valid message for station {station_id_after} never arrived"
    )


def test_missing_required_field_is_skipped(kafka_producer, db):
    # TODO: publish a message missing the station_id key
    # assert consumer keeps running (send a good message after and verify it lands)
    ...


def test_wrong_type_for_temperature_is_skipped(kafka_producer, db):
    # TODO: publish {"station_id": "X", "temperature_c": "not-a-number", "humidity_pct": 50}
    # assert consumer keeps running
    ...
