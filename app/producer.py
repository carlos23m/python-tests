# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
import json
import os
from kafka import KafkaProducer

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "weather-readings")

# Module-level singleton — avoids opening a new broker connection on every request
_producer = None


def _get_producer() -> KafkaProducer:
    """Return the shared KafkaProducer, creating it on first call."""
    global _producer
    # Lazy init: connection is deferred until the first publish so import-time errors
    # (e.g. broker not up yet) don't prevent the app from starting
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
    return _producer


def publish_reading(payload: dict) -> None:
    """Publish one reading dict to Kafka and block until the broker acknowledges it."""
    producer = _get_producer()
    future = producer.send(TOPIC, value=payload)
    future.get(timeout=5)  # block until broker acks; raises on failure
