from datetime import datetime, timezone
import pytest
from src.generator.generation.seasonality import (
    demand_multiplier,
    local_hour
)

def test_local_hour():
    dt = datetime(2026, 1, 6, 18, 30, tzinfo=timezone.utc)
    assert local_hour(dt, "UTC") == 18.5

def test_local_hour_with_timezone():
    dt = datetime(2026, 1, 6, 8, 30, tzinfo=timezone.utc)
    assert local_hour(dt, "Asia/Vladivostok") == 18.5

def test_evening_peak_is_higher_than_night():
    evening = datetime(2026, 1, 6, 18, 30, tzinfo=timezone.utc)
    night = datetime(2026, 1, 6, 3, 30, tzinfo=timezone.utc)
    assert demand_multiplier(evening, "UTC") > demand_multiplier(night, "UTC")

def test_demand_is_always_positive():
    for hour in range(24):
        dt = datetime(2026, 1, 6, hour, tzinfo=timezone.utc)
        assert demand_multiplier(dt, "UTC") > 0

def test_demand_is_deterministic():
    dt = datetime(2026, 1, 6, 18, 30, tzinfo=timezone.utc)
    first = demand_multiplier(dt, "UTC")
    second = demand_multiplier(dt, "UTC")
    assert first == second

def test_friday_evening_is_higher_than_tuesday():
    friday = datetime(2026, 1, 9, 18, 30, tzinfo=timezone.utc)
    tuesday = datetime(2026, 1, 6, 18, 30, tzinfo=timezone.utc)
    assert demand_multiplier(friday, "UTC") > demand_multiplier(tuesday, "UTC")

def test_sunday_morning_is_quieter_than_tuesday():
    sunday = datetime(2026, 1, 11, 8, 30, tzinfo=timezone.utc)
    tuesday = datetime(2026, 1, 6, 8, 30, tzinfo=timezone.utc)
    assert demand_multiplier(sunday, "UTC") < demand_multiplier(tuesday, "UTC")

def test_naive_datetime_raises_error():
    dt = datetime(2026, 1, 6, 18, 30)
    with pytest.raises(ValueError):
        local_hour(dt, "UTC")
