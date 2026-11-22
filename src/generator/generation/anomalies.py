import random
from enum import StrEnum

class AnomalyKind(StrEnum):
    FRAUD_TRIP = "fraud_trip"                # мнимая поездка: очень короткая и очень дорогая
    IMPOSSIBLE_SPEED = "impossible_speed"    # скорость выше физически возможной
    SURGE_SPIKE = "surge_spike"              # аномально высокий surge

class AnomalyPolicy:
    def __init__(self, probability: float, strength: float, rng: random.Random) -> None:
        if probability < 0 or probability > 1:
            raise ValueError("probability must be between 0 and 1")
        if strength <= 0:
            raise ValueError("strength must be greater than 0")

        self._probability = probability
        self._strength = strength
        self._rng = rng

    @property
    def strength(self) -> float:
        return self._strength

    def decide(self) -> AnomalyKind | None:
        value = self._rng.random()

        if value < self._probability:
            return self._rng.choice(list(AnomalyKind))

        return None
