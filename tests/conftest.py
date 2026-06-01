import os
import pytest
import psycopg2
from kafka import KafkaProducer, KafkaConsumer
import json

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://weather:weather@localhost:5432/weather")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "weather-readings")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def base_url():
    return APP_BASE_URL


@pytest.fixture(scope="session")
def db_conn():
    conn = psycopg2.connect(DATABASE_URL)
    yield conn
    conn.close()


@pytest.fixture
def db(db_conn):
    """Per-test: yield a cursor, roll back after so tests don't bleed state."""
    db_conn.autocommit = False
    cur = db_conn.cursor()
    yield cur
    db_conn.rollback()
    cur.close()


@pytest.fixture(scope="session")
def kafka_producer():
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    yield producer
    producer.close()


@pytest.fixture(scope="session")
def kafka_consumer_factory():
    """Returns a factory so each test can get a fresh consumer with its own group."""
    consumers = []

    def _make(group_id: str):
        c = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP,
            group_id=group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda b: json.loads(b.decode("utf-8")),
            consumer_timeout_ms=5000,
        )
        consumers.append(c)
        return c

    yield _make
    for c in consumers:
        c.close()
