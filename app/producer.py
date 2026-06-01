# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
import json
import os
from kafka import KafkaProducer

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "weather-readings")

_producer = None


def _get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
    return _producer


def publish_reading(payload: dict) -> None:
    producer = _get_producer()
    future = producer.send(TOPIC, value=payload)
    future.get(timeout=10)  # block until broker acks; raises on failure
