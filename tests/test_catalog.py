import random
from collections import Counter
from zoneinfo import ZoneInfo

import pytest

from generator.generation.catalog import CityCatalog, service_types, trip_statuses
from generator.models import (
    ServiceCategory,
    ServiceType,
    TripStatus,
    ZoneType,
)

ALL_CITIES = ["Vladivostok", "Moscow", "Novosibirsk", "Kazan", "Yekaterinburg"]


# ---------- создание каталога ----------

def test_unknown_city_raises() -> None:
    with pytest.raises(ValueError, match="Unknown city"):
        CityCatalog(["Atlantis"])


def test_empty_city_list_raises() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        CityCatalog([])


def test_duplicate_city_names_are_ignored() -> None:
    catalog = CityCatalog(["Moscow", "Moscow", "Kazan"])
    assert [c.city_name for c in catalog.cities()] == ["Moscow", "Kazan"]


def test_catalog_contains_requested_cities_only() -> None:
    catalog = CityCatalog(["Kazan"])
    assert [c.city_name for c in catalog.cities()] == ["Kazan"]
    assert all(z.city_id == 4 for z in catalog.zones())


# ---------- идентификаторы ----------

def test_city_and_zone_ids_are_unique() -> None:
    catalog = CityCatalog(ALL_CITIES)
    city_ids = [c.city_id for c in catalog.cities()]
    zone_ids = [z.zone_id for z in catalog.zones()]
    assert len(city_ids) == len(set(city_ids))
    assert len(zone_ids) == len(set(zone_ids))


def test_city_ids_do_not_depend_on_order() -> None:
    direct = CityCatalog(ALL_CITIES)
    reverse = CityCatalog(list(reversed(ALL_CITIES)))
    assert {c.city_name: c.city_id for c in direct.cities()} == {
        c.city_name: c.city_id for c in reverse.cities()
    }


def test_zone_id_is_built_from_city_id() -> None:
    for zone in CityCatalog(ALL_CITIES).zones():
        assert zone.zone_id // 100 == zone.city_id


# ---------- содержимое справочников ----------

def test_all_timezones_are_valid() -> None:
    for city in CityCatalog(ALL_CITIES).cities():
        ZoneInfo(city.tz_name)  # падает, если часовой пояс не существует


def test_every_city_has_enough_distinct_zones() -> None:
    catalog = CityCatalog(ALL_CITIES)
    for city in catalog.cities():
        zones = catalog.zones_of(city.city_id)
        names = [z.zone_name for z in zones]
        assert len(zones) >= 5
        assert len(names) == len(set(names))
        assert all(z.city_id == city.city_id for z in zones)


def test_every_city_has_center_airport_and_three_zone_types() -> None:
    catalog = CityCatalog(ALL_CITIES)
    for city in catalog.cities():
        types = {z.zone_type for z in catalog.zones_of(city.city_id)}
        assert ZoneType.CENTER in types
        assert ZoneType.AIRPORT in types
        assert len(types) >= 3


def test_zones_of_unknown_city_is_empty() -> None:
    assert CityCatalog(["Moscow"]).zones_of(99) == []


def test_returned_lists_are_copies() -> None:
    catalog = CityCatalog(["Moscow"])
    catalog.cities().clear()
    catalog.zones().clear()
    assert len(catalog.cities()) == 1
    assert len(catalog.zones()) > 0


# ---------- выбор города ----------

def test_same_seed_gives_same_cities() -> None:
    catalog = CityCatalog(ALL_CITIES)
    first, second = random.Random(42), random.Random(42)
    assert [catalog.pick_city(first).city_id for _ in range(100)] == [
        catalog.pick_city(second).city_id for _ in range(100)
    ]


def test_different_seeds_give_different_cities() -> None:
    catalog = CityCatalog(ALL_CITIES)
    first, second = random.Random(1), random.Random(2)
    assert [catalog.pick_city(first).city_id for _ in range(100)] != [
        catalog.pick_city(second).city_id for _ in range(100)
    ]


def test_pick_city_shares_follow_demand_weights() -> None:
    catalog = CityCatalog(ALL_CITIES)
    rng = random.Random(42)
    n = 10_000
    counts = Counter(catalog.pick_city(rng).city_id for _ in range(n))
    total_weight = sum(c.demand_weight for c in catalog.cities())
    for city in catalog.cities():
        expected = city.demand_weight / total_weight
        assert abs(counts[city.city_id] / n - expected) < 0.03


def test_single_city_catalog_always_picks_it() -> None:
    catalog = CityCatalog(["Kazan"])
    rng = random.Random(1)
    assert {catalog.pick_city(rng).city_name for _ in range(50)} == {"Kazan"}


# ---------- выбор районов ----------

def test_pick_zones_returns_zones_of_the_same_city() -> None:
    catalog = CityCatalog(ALL_CITIES)
    rng = random.Random(1)
    for city in catalog.cities():
        valid_ids = {z.zone_id for z in catalog.zones_of(city.city_id)}
        for _ in range(200):
            pickup, dropoff = catalog.pick_zones(city.city_id, rng)
            assert pickup in valid_ids
            assert dropoff in valid_ids


def test_pick_zones_same_zone_share_is_about_15_percent() -> None:
    catalog = CityCatalog(["Moscow"])
    rng = random.Random(42)
    n = 10_000
    same = sum(
        1 for _ in range(n)
        if len(set(catalog.pick_zones(2, rng))) == 1
    )
    assert 0.12 <= same / n <= 0.18


def test_pick_zones_is_deterministic_for_same_seed() -> None:
    catalog = CityCatalog(["Moscow"])
    first, second = random.Random(5), random.Random(5)
    assert [catalog.pick_zones(2, first) for _ in range(50)] == [
        catalog.pick_zones(2, second) for _ in range(50)
    ]


def test_pick_zones_unknown_city_id_raises() -> None:
    catalog = CityCatalog(["Moscow"])
    with pytest.raises(ValueError, match="Unknown city_id"):
        catalog.pick_zones(99, random.Random(1))


def test_pick_zones_city_not_in_catalog_raises() -> None:
    catalog = CityCatalog(["Moscow"])  # Владивосток (id=1) не выбран
    with pytest.raises(ValueError, match="Unknown city_id"):
        catalog.pick_zones(1, random.Random(1))


# ---------- типы сервиса и статусы ----------

def test_service_types_match_enum() -> None:
    types = service_types()
    assert [t.service_type_id for t in types] == [1, 2, 3]
    assert [t.service_type_id for t in types] == [
        ServiceType.ECONOMY, ServiceType.COMFORT, ServiceType.DELIVERY
    ]
    assert [t.service_name for t in types] == ["economy", "comfort", "delivery"]


def test_delivery_is_the_only_delivery_category() -> None:
    by_name = {t.service_name: t.category for t in service_types()}
    assert by_name["delivery"] == ServiceCategory.DELIVERY
    assert by_name["economy"] == ServiceCategory.PASSENGER
    assert by_name["comfort"] == ServiceCategory.PASSENGER


def test_service_types_returns_a_copy() -> None:
    service_types().clear()
    assert len(service_types()) == 3


def test_trip_statuses_match_enum() -> None:
    statuses = trip_statuses()
    assert [s.status_id for s in statuses] == [
        TripStatus.COMPLETED, TripStatus.CANCELLED, TripStatus.NO_SHOW
    ]
    assert [s.status_name for s in statuses] == [
        "completed", "cancelled", "no_show"
    ]