"""
Load test for the weather ingest API.
Run against YOUR local app only — never against public servers.

  locust -f tests/performance/locustfile.py --headless \
    -u 50 -r 5 --run-time 120s --host http://localhost:8000
"""
import random
from locust import HttpUser, task, between


def _random_reading():
    return {
        "station_id": f"LOAD-{random.randint(1, 10):03d}",
        "temperature_c": round(random.uniform(-10, 45), 1),
        "humidity_pct": round(random.uniform(0, 100), 1),
    }


class WeatherAPIUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(5)
    def ingest_reading(self):
        """POST a new weather reading — the hot path."""
        self.client.post("/readings", json=_random_reading())

    @task(2)
    def query_readings(self):
        """GET readings for a random station — simulates dashboard polling."""
        station = f"LOAD-{random.randint(1, 10):03d}"
        self.client.get(f"/readings/{station}")

    @task(1)
    def health_check(self):
        self.client.get("/health")
