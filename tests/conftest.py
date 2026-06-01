# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
import os
import time
import pytest
import psycopg2
from kafka import KafkaProducer
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


@pytest.fixture
def wait_for_rows(db):
    """Poll Postgres until at least `expected` rows exist for station_id, or timeout expires."""
    def _wait(station_id: str, expected: int, timeout: int = 20) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            db.execute(
                "SELECT COUNT(*) FROM readings WHERE station_id = %s", (station_id,)
            )
            if db.fetchone()[0] >= expected:
                return
            time.sleep(0.5)
    return _wait


@pytest.fixture(scope="session")
def kafka_producer():
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    yield producer
    producer.close()
