import random
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from generator.generation.pricing import fare
from generator.models import City, ServiceTypeInfo, TripStatus


@dataclass(frozen=True, slots=True)
class TripContext:
    at: datetime
    city: City
    demand: float
    distance_km: float = 0.0
    duration_min: float = 0.0
    surge: float = 1.0
    fare: float = 0.0


def _clamp(value: float, low: float, high: float) -> float:
    """Зажимает значение в заданный интервал йоу"""
    return max(low, min(high, value))


class MetricSampler(ABC):

    @abstractmethod
    def sample(self, ctx: TripContext, rng: random.Random) -> float: ...


class DistanceSampler(MetricSampler):
    """Расстояние поездки, где много коротких и мало длинных(используется логнормальное распределение)"""

    def __init__(self, median_km: float = 6.0, sigma: float = 0.6) -> None:
        self._mu = math.log(median_km)
        self._sigma = sigma

    def sample(self, ctx: TripContext, rng: random.Random) -> float:
        value = rng.lognormvariate(self._mu, self._sigma)
        return round(_clamp(value, 0.5, 80), 2)


class DurationSampler(MetricSampler):
    """Время = расстояние / скорость"""

    def __init__(self, base_speed_kmh: float = 35.0) -> None:
        self._base_speed_kmh = base_speed_kmh

    def sample(self, ctx: TripContext, rng: random.Random) -> float:
        if ctx.distance_km <= 0:
            raise ValueError("Distance km must be set before sampling duration")
        congestion = ctx.city.traffic_factor * (0.8 + 0.2 * ctx.demand)
        speed = self._base_speed_kmh / congestion * rng.gauss(1.0, 0.1)
        speed = _clamp(speed, 8.0, 90.0)
        return round(ctx.distance_km / speed * 60, 2)


class SurgeSampler(MetricSampler):
    """Повышающий коэф который реагирует только при повышенном спросе"""

    def sample(self, ctx: TripContext, rng: random.Random) -> float:
        excess = max(0.0, ctx.demand - 1.2)
        value = 1.0 + 0.8 * excess + abs(rng.gauss(0.0, 0.05))
        return round(_clamp(value, 1.0, 3.0), 2)


class FareSampler(MetricSampler):

    def __init__(self, service: "ServiceTypeInfo") -> None:
        self._service = service

    def sample(self, ctx: TripContext, rng: random.Random) -> float:
        if ctx.distance_km <= 0 or ctx.duration_min <= 0:
            raise ValueError("distance_km and duration_min must be set before fare")

        base_fare = fare(
            ctx.distance_km,
            ctx.duration_min,
            base=self._service.base_fare,
            per_km=self._service.per_km,
            per_min=self._service.per_min,
        )
        return round(base_fare * ctx.surge, 2)


class TipSampler(MetricSampler):
    def __init__(self, tip_probability: float = 0.35) -> None:
        self._tip_probability = tip_probability

    def sample(self, ctx: TripContext, rng: random.Random) -> float:
        if ctx.fare <= 0:
            raise ValueError("fare must be set before sampling tip")
        gives_tip = rng.random() < self._tip_probability
        share = rng.uniform(0.05, 0.2)
        if not gives_tip:
            return 0.0
        return round(share * ctx.fare, 2)


class StatusPicker:
    def __init__(self, base_cancel: float = 0.06, no_show: float = 0.02,
                 surge_sensitivity: float = 0.05, ) -> None:
        self._base_cancel = base_cancel
        self._no_show = no_show
        self._surge_sensitivity = surge_sensitivity

    def sample(self, ctx: TripContext, rng: random.Random) -> TripStatus:
        roll = rng.random()
        cancel_p = self._base_cancel + self._surge_sensitivity * max(
            0.0, ctx.surge - 1.0
        )
        cancel_p = _clamp(cancel_p, 0.0, 0.5)
        no_show_p = _clamp(self._no_show, 0.0, 0.5)
        if cancel_p + no_show_p > 1.0:
            no_show_p = max(0.0, 1.0 - cancel_p)

        if roll < cancel_p:
            return TripStatus.CANCELLED
        if roll < cancel_p + no_show_p:
            return TripStatus.NO_SHOW
        return TripStatus.COMPLETED


class RatingPicker:

    def __init__(self, no_rating_probability: float = 0.3, low_rating_probability: float = 0.08) -> None:
        self._no_rating = no_rating_probability
        self._low_rating = low_rating_probability

    def sample(self, ctx: TripContext, rng: random.Random) -> int:
        has_rating = rng.random() >= self._no_rating
        is_low = rng.random() < self._low_rating
        low_value = rng.choice([1, 2, 3, 3, 4, 4, 4])
        if not has_rating:
            return 0
        if is_low:
            return low_value
        return 5
