import random
import pytest
from datetime import datetime
from generator.models import City
from generator.generation.metrics import (TripContext, DistanceSampler, DurationSampler, SurgeSampler)

def test_distance_sampler():
    city = City(
        city_id=1,
        city_name="Amsterdam",
        tz_name="Europe/Amsterdam",
        traffic_factor=1.2,
        demand_weight=1.0,
    )
    ctx = TripContext(
        at=datetime(2026, 11, 22),
        city=city,
        demand=1.0,
    )
    sampler = DistanceSampler()
    distance = sampler.sample(ctx, random.Random(42))
    assert 0.5 <= distance <= 80

def test_distance_sampler_reproducible():
    city = City(
        city_id=1,
        city_name="Amsterdam",
        tz_name="Europe/Amsterdam",
        traffic_factor=1.2,
        demand_weight=1.0,
    )
    ctx = TripContext(
        at=datetime(2026, 11, 22),
        city=city,
        demand=1.0,
    )
    sampler1 = DistanceSampler()
    sampler2 = DistanceSampler()
    rng1 = random.Random(42)
    rng2 = random.Random(42)
    distance1 = sampler1.sample(ctx, rng1)
    distance2 = sampler2.sample(ctx, rng2)
    assert distance1 == distance2

def test_duration_sampler_without_distance():
    city = City(
        city_id=1,
        city_name="Amsterdam",
        tz_name="Europe/Amsterdam",
        traffic_factor=1.2,
        demand_weight=1.0,
    )
    ctx = TripContext(
        at=datetime(2026, 11, 22),
        city=city,
        demand=1.0,
    )
    sampler = DurationSampler()
    with pytest.raises(ValueError):
        sampler.sample(ctx, random.Random(42))

def test_duration_sampler():
    city = City(
        city_id=1,
        city_name="Amsterdam",
        tz_name="Europe/Amsterdam",
        traffic_factor=1.2,
        demand_weight=1.0,
    )
    ctx = TripContext(
        at=datetime(2026, 11, 22),
        city=city,
        demand=1.0,
        distance_km=10.0,
    )
    sampler = DurationSampler()
    duration = sampler.sample(ctx, random.Random(42))
    assert duration > 0

def test_duration_sampler_reproducible():
    city = City(
        city_id=1,
        city_name="Amsterdam",
        tz_name="Europe/Amsterdam",
        traffic_factor=1.2,
        demand_weight=1.0,
    )
    ctx = TripContext(
        at=datetime(2026, 11, 22),
        city=city,
        demand=1.0,
        distance_km=10.0,
    )
    sampler1 = DurationSampler()
    sampler2 = DurationSampler()
    duration1 = sampler1.sample(ctx, random.Random(42))
    duration2 = sampler2.sample(ctx, random.Random(42))
    assert duration1 == duration2

def test_surge_sampler_minimum():
    city = City(
        city_id=1,
        city_name="Amsterdam",
        tz_name="Europe/Amsterdam",
        traffic_factor=1.2,
        demand_weight=1.0,
    )
    ctx = TripContext(
        at=datetime(2026, 11, 22),
        city=city,
        demand=1.0,
    )
    sampler = SurgeSampler()
    surge = sampler.sample(ctx, random.Random(42))
    assert surge >= 1.0


def test_surge_sampler_maximum():
    city = City(
        city_id=1,
        city_name="Amsterdam",
        tz_name="Europe/Amsterdam",
        traffic_factor=1.2,
        demand_weight=1.0,
    )
    ctx = TripContext(
        at=datetime(2026, 11, 22),
        city=city,
        demand=10.0,
    )
    sampler = SurgeSampler()
    surge = sampler.sample(ctx, random.Random(42))

    assert surge <= 3.0

def test_surge_sampler_reproducible():
    city = City(
        city_id=1,
        city_name="Amsterdam",
        tz_name="Europe/Amsterdam",
        traffic_factor=1.2,
        demand_weight=1.0,
    )
    ctx = TripContext(
        at=datetime(2026, 11, 22),
        city=city,
        demand=2.0,
    )
    sampler1 = SurgeSampler()
    sampler2 = SurgeSampler()
    surge1 = sampler1.sample(ctx, random.Random(42))
    surge2 = sampler2.sample(ctx, random.Random(42))
    assert surge1 == surge2
