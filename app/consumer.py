# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
"""
Run as a standalone process:  python -m app.consumer

Reads weather readings from Kafka and persists each one to Postgres.
A malformed message is logged and skipped — it must NOT crash the consumer.
"""
import json
import logging
import os
from datetime import datetime, timezone
from kafka import KafkaConsumer
from app.models import init_db, insert_reading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "weather-readings")
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "weather-consumer")


def run():
    """
    Start the consumer loop: connect to Kafka, poll indefinitely, persist each reading to Postgres.
    Intended to run as a long-lived process — it only returns if the Kafka connection is closed.
    """
    # Ensure the readings table exists before the loop starts receiving messages
    init_db()

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        # earliest: on first start (or if offsets are lost) replay from the beginning
        # so no messages published before the consumer came up are silently dropped
        auto_offset_reset="earliest",
        # auto-commit gives at-least-once delivery; a message can be re-delivered if the
        # consumer crashes between processing and the next commit interval
        enable_auto_commit=True,
    )

    logger.info("Consumer started — listening on topic '%s'", TOPIC)
    for message in consumer:
        try:
            # Decode manually inside the loop — if value_deserializer were used instead,
            # a JSONDecodeError would be raised before entering the try/except and crash the process
            data = json.loads(message.value.decode("utf-8"))

            # timestamp is optional in the message; fall back to now so the column is never NULL
            raw_ts = data.get("timestamp")

            insert_reading({
                "station_id": data["station_id"],
                # Explicit float() cast so a string value like "20.5" raises ValueError here
                # rather than being silently stored as the wrong type
                "temperature_c": float(data["temperature_c"]),
                "humidity_pct": float(data["humidity_pct"]),
                "timestamp": datetime.fromisoformat(raw_ts) if raw_ts else datetime.now(timezone.utc),
            })
            logger.info("Persisted reading from station %s", data.get("station_id"))
        except Exception:
            # Poison message — log and continue; never crash the loop
            logger.exception("Skipping malformed message: %s", message.value)


if __name__ == "__main__":
    run()
