from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime
from app.models import init_db, save_reading
from app.producer import publish_reading

app = FastAPI(title="Weather Ingest API")


class WeatherReading(BaseModel):
    station_id: str = Field(..., min_length=1)
    temperature_c: float
    humidity_pct: float = Field(..., ge=0, le=100)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


@app.on_event("startup")
def on_startup():
    init_db()


@app.post("/readings", status_code=status.HTTP_202_ACCEPTED)
def ingest_reading(reading: WeatherReading):
    """Accept a weather reading, publish it to Kafka, return 202."""
    try:
        publish_reading(reading.model_dump(mode="json"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "accepted", "station_id": reading.station_id}


@app.get("/readings/{station_id}")
def get_readings(station_id: str, limit: int = 50):
    """Return the last N persisted readings for a station."""
    rows = save_reading(station_id, limit=limit)
    return {"station_id": station_id, "readings": rows}


@app.get("/health")
def health():
    return {"status": "ok"}
