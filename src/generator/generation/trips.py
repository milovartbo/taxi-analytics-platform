import random
import uuid
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import datetime, timedelta

from generator.generation.anomalies import AnomalyKind, AnomalyPolicy
from generator.generation.catalog import CityCatalog
from generator.generation.metrics import (
    DistanceSampler,
    DurationSampler,
    FareSampler,
    RatingPicker,
    StatusPicker,
    SurgeSampler,
    TipSampler,
    TripContext,
)
from generator.generation.pricing import MAX_SPEED_KMH
from generator.models import City, Driver, ServiceType, ServiceTypeInfo, Trip, TripStatus

# demand_multiplier(at, tz_name): время в UTC и название часового пояса города
DemandFn = Callable[[datetime, str], float]

# Нормальный surge не бывает выше 3.0 (см. SurgeSampler), поэтому всплеск
# аномалии всегда выше этого порога: его легко найти в данных.
_SURGE_SPIKE_MIN = 3.5


class TripGenerator:
    """Фасад: собирает одну поездку из готовых частей в нужном порядке."""

    def __init__(
            self,
            catalog: CityCatalog,
            drivers: Sequence[Driver],
            services: Sequence[ServiceTypeInfo],
            anomaly_policy: AnomalyPolicy,
            rng: random.Random,
            demand_fn: DemandFn,
    ) -> None:
        if not drivers:
            raise ValueError("drivers must not be empty")
        self._catalog = catalog
        self._drivers = list(drivers)
        self._anomaly_policy = anomaly_policy
        self._rng = rng
        self._demand_fn = demand_fn

        self._cities: dict[int, City] = {c.city_id: c for c in catalog.cities()}
        self._services: dict[str, ServiceTypeInfo] = {s.service_name: s for s in services}
        # тариф зависит от типа сервиса, поэтому свой FareSampler на каждый тип
        self._fares: dict[str, FareSampler] = {s.service_name: FareSampler(s) for s in services}

        for driver in self._drivers:
            if driver.home_city_id not in self._cities:
                raise ValueError(f"Driver {driver.driver_id}: city {driver.home_city_id} is not in catalog")
            if driver.vehicle_class not in self._services:
                raise ValueError(f"Driver {driver.driver_id}: unknown vehicle_class {driver.vehicle_class}")

        self._distance = DistanceSampler()
        self._duration = DurationSampler()
        self._surge = SurgeSampler()
        self._tip = TipSampler()
        self._status = StatusPicker()
        self._rating = RatingPicker()

    def generate(self, at: datetime) -> Trip:
        rng = self._rng
        strength = self._anomaly_policy.strength

        # Аномалию решаем первой: она меняет значения ДО того, как их
        # используют следующие самплеры (тариф считается уже от них).
        kind = self._anomaly_policy.decide()

        driver = rng.choice(self._drivers)
        city = self._cities[driver.home_city_id]
        service = self._services[driver.vehicle_class]
        pickup_zone_id, dropoff_zone_id = self._catalog.pick_zones(city.city_id, rng)

        ctx = TripContext(at=at, city=city, demand=self._demand_fn(at, city.tz_name))

        # Каждый самплер вызывается всегда. Аномалия только подменяет результат,
        # поэтому число обращений к rng от неё не зависит (кроме её собственных).
        distance = self._distance.sample(ctx, rng)
        if kind is AnomalyKind.FRAUD_TRIP:
            distance = round(rng.uniform(0.3, 1.0), 2)
        ctx = replace(ctx, distance_km=distance)

        duration = self._duration.sample(ctx, rng)
        if kind is AnomalyKind.FRAUD_TRIP:
            duration = round(rng.uniform(3.0, 8.0), 2)
        elif kind is AnomalyKind.IMPOSSIBLE_SPEED:
            speed = MAX_SPEED_KMH + strength * rng.uniform(20.0, 60.0)
            duration = max(0.01, round(distance / speed * 60, 2))
        ctx = replace(ctx, duration_min=duration)

        surge = self._surge.sample(ctx, rng)
        if kind is AnomalyKind.SURGE_SPIKE:
            surge = round(max(_SURGE_SPIKE_MIN, surge * strength * rng.uniform(1.5, 2.5)), 2)
        ctx = replace(ctx, surge=surge)

        fare = self._fares[service.service_name].sample(ctx, rng)
        if kind is AnomalyKind.FRAUD_TRIP:
            fare = round(fare * strength * rng.uniform(3.0, 6.0), 2)
        ctx = replace(ctx, fare=fare)

        status = self._status.sample(ctx, rng)
        tip = self._tip.sample(ctx, rng)
        rating = self._rating.sample(ctx, rng)

        if kind is not None:
            # Аномальная поездка всегда завершена: иначе правило зерна
            # обнулило бы деньги и сам признак аномалии пропал бы.
            status = TripStatus.COMPLETED
        elif status != TripStatus.COMPLETED:
            fare, tip, rating = 0.0, 0.0, 0

        # UUID из своего rng, а не из uuid4(): иначе нельзя воспроизвести по seed
        trip_id = uuid.UUID(int=rng.getrandbits(128), version=4)

        return Trip(
            trip_id=trip_id,
            started_at=at,
            driver_id=driver.driver_id,
            city_id=city.city_id,
            pickup_zone_id=pickup_zone_id,
            dropoff_zone_id=dropoff_zone_id,
            service_type_id=ServiceType(service.service_type_id),
            status_id=status,
            distance_km=distance,
            duration_min=duration,
            surge=surge,
            fare=fare,
            tip=tip,
            trip_rating=rating,
            is_anomaly=kind is not None,
        )


class BatchGenerator:
    """Пачка поездок: размер зависит от спроса (суточная сезонность)."""

    def __init__(
            self,
            generator: TripGenerator,
            cities: Sequence[City],
            demand_fn: DemandFn,
            rng: random.Random,
            base_batch_size: int = 50,
            interval_seconds: float = 1.0,
    ) -> None:
        if not cities:
            raise ValueError("cities must not be empty")
        if base_batch_size <= 0:
            raise ValueError("base_batch_size must be positive")
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self._generator = generator
        self._cities = list(cities)
        self._demand_fn = demand_fn
        self._rng = rng
        self._base_batch_size = base_batch_size
        self._interval_seconds = interval_seconds

    def batch_size(self, at: datetime) -> int:
        """Базовый размер, умноженный на средний спрос (город весит по demand_weight)."""
        total_weight = sum(c.demand_weight for c in self._cities)
        mean_demand = sum(
            c.demand_weight * self._demand_fn(at, c.tz_name) for c in self._cities
        ) / total_weight
        return max(1, round(self._base_batch_size * mean_demand))

    def generate_batch(self, at: datetime) -> list[Trip]:
        trips: list[Trip] = []
        for _ in range(self.batch_size(at)):
            # поездки разбросаны по интервалу, а не стоят в одну секунду
            offset = self._rng.uniform(0.0, self._interval_seconds)
            trips.append(self._generator.generate(at + timedelta(seconds=offset)))
        trips.sort(key=lambda trip: trip.started_at)
        return trips
