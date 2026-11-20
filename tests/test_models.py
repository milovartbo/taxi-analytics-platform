from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest

from generator.models import (
    City,
    Driver,
    ServiceCategory,
    ServiceType,
    ServiceTypeInfo,
    Trip,
    TripStatus,
    TripStatusInfo,
    Zone,
    ZoneType,
)

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)


# ---------- фабрики корректных объектов ----------
# Каждый тест меняет только то поле, которое проверяет.

def make_trip(**overrides: Any) -> Trip:
    fields: dict[str, Any] = {
        "trip_id": uuid4(),
        "started_at": NOW,
        "driver_id": 1,
        "city_id": 1,
        "pickup_zone_id": 101,
        "dropoff_zone_id": 102,
        "service_type_id": ServiceType.ECONOMY,
        "status_id": TripStatus.COMPLETED,
        "distance_km": 10.0,
        "duration_min": 20.0,
        "surge": 1.0,
        "fare": 560.0,
        "tip": 50.0,
        "trip_rating": 5,
        "is_anomaly": False,
    }
    fields.update(overrides)
    return Trip(**fields)


def make_driver(**overrides: Any) -> Driver:
    fields: dict[str, Any] = {
        "driver_id": 1,
        "full_name": "Иван Петров",
        "home_city_id": 1,
        "vehicle_class": "economy",
        "driver_rating": 4.8,
        "registered_at": NOW,
    }
    fields.update(overrides)
    return Driver(**fields)


def make_city(**overrides: Any) -> City:
    fields: dict[str, Any] = {
        "city_id": 1,
        "city_name": "Vladivostok",
        "tz_name": "Asia/Vladivostok",
        "traffic_factor": 1.2,
        "demand_weight": 0.5,
    }
    fields.update(overrides)
    return City(**fields)


def make_zone(**overrides: Any) -> Zone:
    fields: dict[str, Any] = {
        "zone_id": 101,
        "city_id": 1,
        "zone_name": "Центр",
        "zone_type": ZoneType.CENTER,
    }
    fields.update(overrides)
    return Zone(**fields)


def make_service_type(**overrides: Any) -> ServiceTypeInfo:
    fields: dict[str, Any] = {
        "service_type_id": 1,
        "service_name": "economy",
        "category": ServiceCategory.PASSENGER,
        "base_fare": 100.0,
        "per_km": 30.0,
        "per_min": 8.0,
    }
    fields.update(overrides)
    return ServiceTypeInfo(**fields)


# ---------- Trip ----------

def test_valid_completed_trip_is_created() -> None:
    trip = make_trip()
    assert trip.status_id == TripStatus.COMPLETED
    assert trip.fare == 560.0


def test_completed_trip_without_rating_is_valid() -> None:
    assert make_trip(trip_rating=0).trip_rating == 0


def test_cancelled_trip_with_zero_money_is_valid() -> None:
    trip = make_trip(
        status_id=TripStatus.CANCELLED, fare=0.0, tip=0.0, trip_rating=0
    )
    assert trip.status_id == TripStatus.CANCELLED


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"distance_km": 0}, "Distance must be positive"),
        ({"distance_km": -5}, "Distance must be positive"),
        ({"duration_min": 0}, "Duration min must be positive"),
        ({"surge": 0.9}, "Surge must be at least 1"),
        ({"fare": -1}, "Fare must be positive"),
        ({"tip": -1}, "Tip must be positive"),
        ({"trip_rating": 6}, "Trip rating must be between 0 and 5"),
        ({"trip_rating": -1}, "Trip rating must be between 0 and 5"),
        ({"pickup_zone_id": 0}, "Pickup zone id must be positive"),
        ({"dropoff_zone_id": 0}, "Dropoff zone id must be positive"),
    ],
)
def test_invalid_trip_raises(overrides: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        make_trip(**overrides)


@pytest.mark.parametrize("status", [TripStatus.CANCELLED, TripStatus.NO_SHOW])
@pytest.mark.parametrize(
    "money", [{"fare": 100.0}, {"tip": 10.0}, {"trip_rating": 3}]
)
def test_not_completed_trip_cannot_have_money_or_rating(
    status: TripStatus, money: dict[str, Any]
) -> None:
    overrides: dict[str, Any] = {
        "fare": 0.0, "tip": 0.0, "trip_rating": 0, **money
    }
    with pytest.raises(ValueError, match="Only completed trips"):
        make_trip(status_id=status, **overrides)


def test_trip_is_frozen() -> None:
    trip = make_trip()
    with pytest.raises(FrozenInstanceError):
        trip.fare = 1.0  # type: ignore[misc]


# ---------- Driver ----------

def test_valid_driver_is_created() -> None:
    assert make_driver().full_name == "Иван Петров"


@pytest.mark.parametrize("rating", [0.5, 6.0])
def test_driver_rating_out_of_range_raises(rating: float) -> None:
    with pytest.raises(ValueError, match="Driver rating"):
        make_driver(driver_rating=rating)


def test_driver_id_must_be_positive() -> None:
    with pytest.raises(ValueError, match="driver_id"):
        make_driver(driver_id=0)


def test_driver_home_city_id_must_be_positive() -> None:
    with pytest.raises(ValueError, match="Home City id"):
        make_driver(home_city_id=0)


# ---------- City ----------

def test_valid_city_is_created() -> None:
    assert make_city().tz_name == "Asia/Vladivostok"


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"city_id": 0}, "city_id"),
        ({"city_name": ""}, "City name"),
        ({"city_name": "   "}, "City name"),
        ({"traffic_factor": 0}, "Traffic factor"),
        ({"demand_weight": 0}, "Demand weight"),
    ],
)
def test_invalid_city_raises(overrides: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        make_city(**overrides)


# ---------- Zone ----------

@pytest.mark.parametrize("zone_type", list(ZoneType))
def test_zone_is_created_for_every_zone_type(zone_type: ZoneType) -> None:
    assert make_zone(zone_type=zone_type).zone_type == zone_type


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"zone_id": 0}, "zone_id"),
        ({"city_id": 0}, "city_id"),
        ({"zone_name": ""}, "Zone name"),
        ({"zone_name": "   "}, "Zone name"),
    ],
)
def test_invalid_zone_raises(overrides: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        make_zone(**overrides)


# ---------- ServiceTypeInfo ----------

def test_valid_service_type_is_created() -> None:
    assert make_service_type().category == ServiceCategory.PASSENGER


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"service_name": ""}, "Service type name"),
        ({"service_name": "   "}, "Service type name"),
        ({"base_fare": 0}, "Base fare"),
        ({"per_km": 0}, "Per-km"),
        ({"per_min": 0}, "Per-min"),
    ],
)
def test_invalid_service_type_raises(
    overrides: dict[str, Any], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        make_service_type(**overrides)


# ---------- TripStatusInfo ----------

def test_valid_trip_status_info_is_created() -> None:
    info = TripStatusInfo(status_id=1, status_name="completed")
    assert info.status_name == "completed"


@pytest.mark.parametrize(
    "status_id, status_name, message",
    [(0, "completed", "status_id"), (1, "   ", "Status name")],
)
def test_invalid_trip_status_info_raises(
    status_id: int, status_name: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        TripStatusInfo(status_id=status_id, status_name=status_name)


# ---------- Enum: значения — это контракт со схемой ClickHouse ----------

def test_service_type_ids_match_dimension_table() -> None:
    assert ServiceType.ECONOMY == 1
    assert ServiceType.COMFORT == 2
    assert ServiceType.DELIVERY == 3


def test_trip_status_ids_match_dimension_table() -> None:
    assert TripStatus.COMPLETED == 1
    assert TripStatus.CANCELLED == 2
    assert TripStatus.NO_SHOW == 3


def test_service_category_values() -> None:
    assert {c.value for c in ServiceCategory} == {"passenger", "delivery"}


def test_zone_type_values() -> None:
    assert {z.value for z in ZoneType} == {
        "center", "residential", "airport", "industrial"
    }