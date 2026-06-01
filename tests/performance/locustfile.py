# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
"""
Load test for the weather ingest API.
Run against YOUR local app only — never against public servers.

  locust -f tests/performance/locustfile.py --headless \
    -u 50 -r 5 --run-time 120s --host http://localhost:8000
"""
import random
from locust import HttpUser, task, between


def _random_reading():
    # 10 synthetic stations keep IDs short and predictable for assertions
    # Temperature range covers realistic weather extremes (-10 °C to 45 °C)
    # Humidity is the full valid model range (0–100 %) to stress boundary handling
    return {
        "station_id": f"LOAD-{random.randint(1, 10):03d}",
        "temperature_c": round(random.uniform(-10, 45), 1),
        "humidity_pct": round(random.uniform(0, 100), 1),
    }


class WeatherAPIUser(HttpUser):
    # Simulates a realistic think-time between requests (100–500 ms)
    wait_time = between(0.1, 0.5)

    # Task weights mirror expected production traffic: 5 writes : 2 reads : 1 health
    # POST is the hot path — ingestion load dominates over query and health traffic

    @task(5)
    def ingest_reading(self):
        """POST a new weather reading — the hot path."""
        self.client.post("/readings", json=_random_reading())

    @task(2)
    def query_readings(self):
        """GET readings for a random station — simulates dashboard polling."""
        # Reuse the same station pool as ingest so GET requests hit existing rows
        station = f"LOAD-{random.randint(1, 10):03d}"
        self.client.get(f"/readings/{station}")

    @task(1)
    def health_check(self):
        # Verifies the liveness endpoint stays responsive under concurrent write load
        self.client.get("/health")
