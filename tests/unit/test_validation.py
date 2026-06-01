# Designed and created by Carlos Mendez - www.linkedin.com/in/carlos-mendez1 - CR - 2026
"""
Unit tests for input validation in the WeatherReading model.
No I/O — these run without Docker.
"""
import pytest
from pydantic import ValidationError
from app.main import WeatherReading


def test_valid_reading_parses_correctly():
    r = WeatherReading(station_id="S01", temperature_c=22.5, humidity_pct=60.0)
    assert r.station_id == "S01"
    assert r.temperature_c == 22.5


def test_humidity_above_100_is_rejected():
    with pytest.raises(ValidationError):
        WeatherReading(station_id="S01", temperature_c=22.0, humidity_pct=101)


def test_humidity_below_0_is_rejected():
    with pytest.raises(ValidationError):
        WeatherReading(station_id="S01", temperature_c=22.0, humidity_pct=-1)


def test_empty_station_id_is_rejected():
    with pytest.raises(ValidationError):
        WeatherReading(station_id="", temperature_c=22.0, humidity_pct=50)


def test_missing_temperature_is_rejected():
    with pytest.raises(ValidationError):
        WeatherReading(station_id="S01", humidity_pct=50)


def test_negative_temperature_is_valid():
    # Below-zero temps are physically valid
    r = WeatherReading(station_id="S01", temperature_c=-10.0, humidity_pct=80)
    assert r.temperature_c == -10.0


def test_boundary_humidity_0_is_valid():
    r = WeatherReading(station_id="S01", temperature_c=0.0, humidity_pct=0)
    assert r.humidity_pct == 0


def test_boundary_humidity_100_is_valid():
    r = WeatherReading(station_id="S01", temperature_c=0.0, humidity_pct=100)
    assert r.humidity_pct == 100
