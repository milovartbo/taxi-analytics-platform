import pytest

from generator.generation.pricing import (
    average_fare,
    fare,
    fare_with_surge,
    is_suspicious,
    speed_kmh,
)


def test_speed_kmh() -> None:
    assert speed_kmh(60, 60) == 60


def test_fare() -> None:
    assert fare(10, 20) == 560  # 100 + 10*30 + 20*8


def test_fare_with_surge() -> None:
    assert fare_with_surge(10, 20, surge=2.0) == pytest.approx(1120)


@pytest.mark.parametrize("distance, minutes", [(0, 10), (10, 0), (-1, 5)])
def test_invalid_trip_raises(distance: float, minutes: float) -> None:
    with pytest.raises(ValueError):
        speed_kmh(distance, minutes)


def test_normal_trip_is_not_suspicious() -> None:
    assert is_suspicious(10, 20, 560) is False


def test_too_fast_is_suspicious() -> None:
    assert is_suspicious(100, 30, 1000) is True  # 200 км/ч


def test_too_expensive_per_km_is_suspicious() -> None:
    assert is_suspicious(1, 10, 600) is True  # 600 ₽ за км


def test_average_fare() -> None:
    assert average_fare([100, 200]) == 150


def test_average_fare_empty_list() -> None:
    assert average_fare([]) is None
