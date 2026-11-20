import random
from zoneinfo import ZoneInfo
import pytest
from generator.generation.catalog import CityCatalog, service_types
from generator.models import ServiceCategory, ServiceType, ZoneType

ALL_CITIES = [
    "Vladivostok",
    "Moscow",
    "Novosibirsk",
    "Kazan",
    "Yekaterinburg",
]

@pytest.fixture
def catalog() -> CityCatalog:
    return CityCatalog(ALL_CITIES)

def test_unknown_city_raises_value_error() -> None:
    with pytest.raises(ValueError):
        CityCatalog(["UnknownCity"])

def test_city_and_zone_ids_are_unique(catalog: CityCatalog) -> None:
    city_ids = [city.city_id for city in catalog.cities()]
    zone_ids = [zone.zone_id for zone in catalog.zones()]
    assert len(city_ids) == len(set(city_ids))
    assert len(zone_ids) == len(set(zone_ids))

def test_city_ids_do_not_depend_on_order() -> None:
    first = CityCatalog(["Moscow", "Kazan"])
    second = CityCatalog(["Kazan", "Moscow"])
    first_ids = {city.city_name: city.city_id for city in first.cities()}
    second_ids = {city.city_name: city.city_id for city in second.cities()}
    assert first_ids == second_ids

def test_all_timezones_are_valid(catalog: CityCatalog) -> None:
    for city in catalog.cities():
        assert ZoneInfo(city.tz_name)

def test_every_city_has_at_least_five_zones(
    catalog: CityCatalog,
) -> None:
    for city in catalog.cities():
        zones = catalog.zones_of(city.city_id)
        assert len(zones) >= 5
        assert len({zone.zone_name for zone in zones}) == len(zones)
        assert all(zone.city_id == city.city_id for zone in zones)
        zone_types = {zone.zone_type for zone in zones}
        assert ZoneType.CENTER in zone_types
        assert ZoneType.AIRPORT in zone_types
        assert len(zone_types) >= 3

def test_city_sequence_is_reproducible(
    catalog: CityCatalog,
) -> None:
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    sequence1 = [
        catalog.pick_city(rng1).city_id
        for _ in range(100)
    ]
    sequence2 = [
        catalog.pick_city(rng2).city_id
        for _ in range(100)
    ]
    assert sequence1 == sequence2

def test_city_distribution_matches_weights(
    catalog: CityCatalog,
) -> None:
    rng = random.Random(42)
    iterations = 10_000
    counts = {
        city.city_id: 0
        for city in catalog.cities()
    }
    for _ in range(iterations):
        city = catalog.pick_city(rng)
        counts[city.city_id] += 1
    total_weight = sum(
        city.demand_weight
        for city in catalog.cities()
    )
    for city in catalog.cities():
        expected = city.demand_weight / total_weight
        actual = counts[city.city_id] / iterations
        assert abs(actual - expected) <= 0.03

def test_pick_zones_returns_zones_from_same_city(
    catalog: CityCatalog,
) -> None:
    rng = random.Random(42)
    for city in catalog.cities():
        valid_zone_ids = {
            zone.zone_id
            for zone in catalog.zones_of(city.city_id)
        }
        for _ in range(100):
            pickup, dropoff = catalog.pick_zones(city.city_id, rng)
            assert pickup in valid_zone_ids
            assert dropoff in valid_zone_ids

def test_same_zone_probability_is_about_fifteen_percent(
    catalog: CityCatalog,
) -> None:
    rng = random.Random(42)
    city_id = 2
    iterations = 10_000
    same_zone_count = 0
    for _ in range(iterations):
        pickup, dropoff = catalog.pick_zones(city_id, rng)
        if pickup == dropoff:
            same_zone_count += 1
    probability = same_zone_count / iterations
    assert 0.12 <= probability <= 0.18

def test_service_types() -> None:
    services = service_types()
    assert len(services) == 3
    assert [service.service_type_id for service in services] == [
        ServiceType.ECONOMY,
        ServiceType.COMFORT,
        ServiceType.DELIVERY,
    ]
    assert services[0].category == ServiceCategory.PASSENGER
    assert services[1].category == ServiceCategory.PASSENGER
    assert services[2].category == ServiceCategory.DELIVERY
    assert [
        (service.base_fare, service.per_km, service.per_min)
        for service in services
    ] == [
        (100.0, 30.0, 8.0),
        (150.0, 40.0, 12.0),
        (80.0, 22.0, 6.0),
    ]
