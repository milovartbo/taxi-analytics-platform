import random
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from generator.models import City


@dataclass(frozen=True, slots=True)
class TripContext:
    at: datetime
    city: City
    demand: float
    distance_km: float = 0.0
    duration_min: float = 0.0
    surge: float = 1.0


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
