import random
from datetime import datetime, timedelta, timezone, tzinfo
import pytest
from generator.generation.catalog import CityCatalog
from generator.generation.drivers import generate_drivers
from generator.models import Driver

class InvalidTimezone(tzinfo):
    def utcoffset(self, dt):
        return None

    def dst(self, dt):
        return None

@pytest.fixture
def catalog() -> CityCatalog:
    return CityCatalog([
        "Vladivostok",
        "Moscow",
        "Novosibirsk",
        "Kazan",
        "Yekaterinburg"
    ])

@pytest.fixture
def now() -> datetime:
    return datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)

def test_generate_drivers_count_and_ids(
    catalog: CityCatalog,
    now: datetime
) -> None:
    drivers = generate_drivers(
        count=10,
        catalog=catalog,
        rng=random.Random(42),
        now=now
    )
    assert len(drivers) == 10
    assert all(isinstance(driver, Driver) for driver in drivers)
    assert [driver.driver_id for driver in drivers] == list(range(1, 11))

@pytest.mark.parametrize("count", [0, -1, -10])
def test_generate_drivers_invalid_count(
    count: int,
    catalog: CityCatalog,
    now: datetime
) -> None:
    with pytest.raises(ValueError):
        generate_drivers(count, catalog, random.Random(42), now)

def test_generate_drivers_naive_datetime(
    catalog: CityCatalog,
) -> None:
    naive_now = datetime(2026, 11, 25, 12, 0)
    with pytest.raises(ValueError):
        generate_drivers(
            10,
            catalog,
            random.Random(42),
            naive_now
        )

def test_generate_drivers_invalid_timezone(
    catalog: CityCatalog,
) -> None:
    invalid_now = datetime(
        2026, 11, 25, 12, 0,
        tzinfo=InvalidTimezone()
    )
    with pytest.raises(ValueError):
        generate_drivers(
            10,
            catalog,
            random.Random(42),
            invalid_now,
        )

def test_generate_drivers_same_seed_same_result(
    catalog: CityCatalog,
    now: datetime
) -> None:
    drivers_first = generate_drivers(
        100,
        catalog,
        random.Random(42),
        now
    )
    drivers_second = generate_drivers(
        100,
        catalog,
        random.Random(42),
        now
    )
    assert drivers_first == drivers_second

def test_generate_drivers_only_catalog_cities(
    catalog: CityCatalog,
    now: datetime
) -> None:
    drivers = generate_drivers(
        500,
        catalog,
        random.Random(42),
        now
    )
    allowed_city_ids = {
        city.city_id for city in catalog.cities()
    }
    assert all(
        driver.home_city_id in allowed_city_ids
        for driver in drivers
    )

def test_generate_drivers_city_distribution(
    catalog: CityCatalog,
    now: datetime
) -> None:
    drivers = generate_drivers(
        5000,
        catalog,
        random.Random(42),
        now
    )
    weights = {
        city.city_id: city.demand_weight
        for city in catalog.cities()
    }
    total_weight = sum(weights.values())
    for city_id, weight in weights.items():
        expected_ratio = weight / total_weight
        actual_ratio = sum(
            driver.home_city_id == city_id
            for driver in drivers
        ) / len(drivers)
        assert abs(actual_ratio - expected_ratio) < 0.03

def test_generate_drivers_vehicle_distribution(
    catalog: CityCatalog,
    now: datetime,
) -> None:
    drivers = generate_drivers(
        5000,
        catalog,
        random.Random(42),
        now
    )
    expected_ratios = {
        "economy": 0.60,
        "comfort": 0.25,
        "delivery": 0.15
    }
    for vehicle_class, expected_ratio in expected_ratios.items():
        actual_ratio = sum(
            driver.vehicle_class == vehicle_class
            for driver in drivers
        ) / len(drivers)
        assert abs(actual_ratio - expected_ratio) < 0.04

def test_generate_drivers_rating_and_registration_bounds(
    catalog: CityCatalog,
    now: datetime
) -> None:
    drivers = generate_drivers(
        500,
        catalog,
        random.Random(42),
        now
    )
    five_years_ago = now - timedelta(days=5 * 365)
    for driver in drivers:
        assert 3.5 <= driver.driver_rating <= 5.0
        assert driver.driver_rating == round(driver.driver_rating, 2)
        assert five_years_ago <= driver.registered_at <= now
        assert driver.registered_at.tzinfo is not None
        assert driver.registered_at.utcoffset() is not None

def test_generate_drivers_names_are_not_empty_and_diverse(
    catalog: CityCatalog,
    now: datetime,
) -> None:
    drivers = generate_drivers(
        500,
        catalog,
        random.Random(42),
        now
    )
    names = [driver.full_name for driver in drivers]
    assert all(name.strip() for name in names)
    assert len(set(names)) >= 100
