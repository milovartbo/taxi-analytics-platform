MAX_SPEED_KMH = 150
MAX_PRICE_PER_KM = 500


def validate_trip(distance_km: float, minutes: float) -> None:
    if minutes <= 0 or distance_km <= 0:
        raise ValueError('Trip and minutes must be positive')


def speed_kmh(distance_km: float, minutes: float) -> float:
    validate_trip(distance_km, minutes)
    return distance_km / (minutes / 60)


def fare(distance_km: float, minutes: float, base: float = 100.0, per_km: float = 30.0,
         per_min: float = 8.0) -> float:
    validate_trip(distance_km, minutes)
    return base + distance_km * per_km + minutes * per_min


def fare_with_surge(distance_km: float, minutes: float, surge: float = 1.2) -> float:
    return fare(distance_km, minutes) * surge


def is_suspicious(distance_km: float, minutes: float, price: float) -> bool:
    if speed_kmh(distance_km, minutes) > MAX_SPEED_KMH or (price / distance_km) > MAX_PRICE_PER_KM:
        return True
    else:
        return False


def average_fare(fares: list[float]) -> float | None:
    if not fares:
        return None
    return sum(fares) / len(fares)
