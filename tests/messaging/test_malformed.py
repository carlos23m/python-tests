# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
"""
Poison-message tests: malformed messages on the topic must NOT crash the consumer.
The consumer should log the error, skip the bad message, and keep processing.
"""
import os
import uuid
import pytest
from kafka import KafkaProducer

TOPIC = os.getenv("KAFKA_TOPIC", "weather-readings")
DRAIN_TIMEOUT_S = 20


@pytest.fixture(scope="module")
def raw_producer():
    """Producer that sends raw bytes — lets us craft truly malformed payloads."""
    producer = KafkaProducer(bootstrap_servers="localhost:9092")
    yield producer
    producer.close()


def _good_payload(station_id: str) -> dict:
    """Return a valid reading dict used as a sentinel after each poison message."""
    return {
        "station_id": station_id,
        "temperature_c": 20.0,
        "humidity_pct": 50.0,
        "timestamp": "2026-07-01T00:00:00",
    }


def _assert_survived(db, station_id_after: str) -> None:
    """Assert the sentinel row arrived — proves the consumer kept running after the poison message."""
    db.execute(
        "SELECT COUNT(*) FROM readings WHERE station_id = %s", (station_id_after,)
    )
    assert db.fetchone()[0] == 1, (
        f"Consumer crashed — valid message for {station_id_after} never arrived"
    )


# ── Invalid JSON ───────────────────────────────────────────────────────────────

def test_consumer_survives_poison_message_and_processes_next(
    raw_producer, kafka_producer, db, wait_for_rows
):
    """Invalid JSON is skipped; the following valid message is still processed."""
    station_id_after = f"after-poison-{uuid.uuid4().hex[:8]}"

    raw_producer.send(TOPIC, value=b"THIS IS NOT JSON {{{}}")
    raw_producer.flush()
    kafka_producer.send(TOPIC, value=_good_payload(station_id_after))
    kafka_producer.flush()

    wait_for_rows(station_id_after, 1, timeout=DRAIN_TIMEOUT_S)
    _assert_survived(db, station_id_after)


def test_empty_bytes_message_is_skipped(raw_producer, kafka_producer, db, wait_for_rows):
    """An empty byte payload is skipped; the consumer keeps running."""
    station_id_after = f"after-empty-{uuid.uuid4().hex[:8]}"

    raw_producer.send(TOPIC, value=b"")
    raw_producer.flush()
    kafka_producer.send(TOPIC, value=_good_payload(station_id_after))
    kafka_producer.flush()

    wait_for_rows(station_id_after, 1, timeout=DRAIN_TIMEOUT_S)
    _assert_survived(db, station_id_after)


def test_json_array_message_is_skipped(raw_producer, kafka_producer, db, wait_for_rows):
    """Valid JSON but wrong shape — a list instead of an object causes KeyError on station_id."""
    station_id_after = f"after-array-{uuid.uuid4().hex[:8]}"

    raw_producer.send(TOPIC, value=b"[1, 2, 3]")
    raw_producer.flush()
    kafka_producer.send(TOPIC, value=_good_payload(station_id_after))
    kafka_producer.flush()

    wait_for_rows(station_id_after, 1, timeout=DRAIN_TIMEOUT_S)
    _assert_survived(db, station_id_after)


def test_null_json_message_is_skipped(raw_producer, kafka_producer, db, wait_for_rows):
    """JSON null deserialises to None — subscripting it raises TypeError."""
    station_id_after = f"after-null-{uuid.uuid4().hex[:8]}"

    raw_producer.send(TOPIC, value=b"null")
    raw_producer.flush()
    kafka_producer.send(TOPIC, value=_good_payload(station_id_after))
    kafka_producer.flush()

    wait_for_rows(station_id_after, 1, timeout=DRAIN_TIMEOUT_S)
    _assert_survived(db, station_id_after)


# ── Missing / wrong-typed fields ───────────────────────────────────────────────

def test_missing_required_field_is_skipped(kafka_producer, db, wait_for_rows):
    """A message without station_id raises KeyError in the consumer — it must be caught and skipped."""
    station_id_after = f"after-missing-{uuid.uuid4().hex[:8]}"

    kafka_producer.send(TOPIC, value={"temperature_c": 20.0, "humidity_pct": 50.0})
    kafka_producer.flush()
    kafka_producer.send(TOPIC, value=_good_payload(station_id_after))
    kafka_producer.flush()

    wait_for_rows(station_id_after, 1, timeout=DRAIN_TIMEOUT_S)
    _assert_survived(db, station_id_after)


def test_wrong_type_for_temperature_is_skipped(kafka_producer, db, wait_for_rows):
    """A string temperature raises ValueError on float() cast — must be caught and skipped."""
    station_id_after = f"after-badtype-{uuid.uuid4().hex[:8]}"

    kafka_producer.send(
        TOPIC,
        value={
            "station_id": "bad-type-station",
            "temperature_c": "not-a-number",
            "humidity_pct": 50.0,
            "timestamp": "2026-07-01T00:00:00",
        },
    )
    kafka_producer.flush()
    kafka_producer.send(TOPIC, value=_good_payload(station_id_after))
    kafka_producer.flush()

    wait_for_rows(station_id_after, 1, timeout=DRAIN_TIMEOUT_S)
    _assert_survived(db, station_id_after)


# ── Data-quality gap (documentation test) ────────────────────────────────────

def test_out_of_range_humidity_is_persisted_without_validation(
    kafka_producer, db, wait_for_rows
):
    """Consumer has no range validation — humidity_pct > 100 bypasses the HTTP layer
    and is persisted as-is when injected directly into Kafka."""
    station_id = f"range-gap-{uuid.uuid4().hex[:8]}"

    kafka_producer.send(
        TOPIC,
        value={
            "station_id": station_id,
            "temperature_c": 20.0,
            "humidity_pct": 150.0,
            "timestamp": "2026-07-01T00:00:00",
        },
    )
    kafka_producer.flush()

    wait_for_rows(station_id, 1, timeout=DRAIN_TIMEOUT_S)

    db.execute(
        "SELECT humidity_pct FROM readings WHERE station_id = %s", (station_id,)
    )
    row = db.fetchone()
    assert row is not None, f"Row for {station_id} never arrived"
    assert row[0] == 150.0
