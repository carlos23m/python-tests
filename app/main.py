# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.models import init_db, get_recent_readings
from app.producer import publish_reading


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create DB tables on startup; nothing to clean up on shutdown."""
    init_db()
    yield


app = FastAPI(title="Weather Ingest API", lifespan=lifespan)


class WeatherReading(BaseModel):
    station_id: str = Field(..., min_length=1)
    temperature_c: float
    humidity_pct: float = Field(..., ge=0, le=100)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # defaults to now if omitted by caller


@app.post("/readings", status_code=status.HTTP_202_ACCEPTED)
def ingest_reading(reading: WeatherReading):
    """Accept a weather reading, publish it to Kafka, return 202."""
    # 202 not 201: persistence is async — the consumer writes to DB after Kafka delivery
    try:
        publish_reading(reading.model_dump(mode="json"))
    except Exception as exc:
        # Publish failure is an infrastructure problem, not a client input error
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "accepted", "station_id": reading.station_id}


@app.get("/readings/{station_id}")
def get_readings(station_id: str, limit: int = 50):
    """Return the last N persisted readings for a station."""
    rows = get_recent_readings(station_id, limit=limit)
    return {"station_id": station_id, "readings": rows}


@app.get("/health")
def health():
    """Liveness probe — returns 200 as long as the process is running."""
    return {"status": "ok"}
