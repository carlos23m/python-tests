# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
import os
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://weather:weather@localhost:5432/weather")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String, nullable=False, index=True)
    temperature_c = Column(Float, nullable=False)
    humidity_pct = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_recent_readings(station_id: str, limit: int = 50):
    with SessionLocal() as session:
        rows = (
            session.query(Reading)
            .filter_by(station_id=station_id)
            .order_by(Reading.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "station_id": r.station_id,
                "temperature_c": r.temperature_c,
                "humidity_pct": r.humidity_pct,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in rows
        ]


def insert_reading(data: dict):
    with SessionLocal() as session:
        row = Reading(**data)
        session.add(row)
        session.commit()
