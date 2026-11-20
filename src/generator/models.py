from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, IntEnum
from uuid import UUID


class ServiceType(IntEnum):
    ECONOMY = 1
    COMFORT = 2
    DELIVERY = 3


class ServiceCategory(StrEnum):
    PASSENGER = "passenger"
    DELIVERY = "delivery"


class ZoneType(StrEnum):
    CENTER = "center"
    RESIDENTIAL = "residential"
    AIRPORT = "airport"
    INDUSTRIAL = "industrial"


class TripStatus(IntEnum):
    COMPLETED = 1
    CANCELLED = 2
    NO_SHOW = 3


@dataclass(frozen=True, slots=True)
class Driver:
    driver_id: int
    full_name: str
    home_city_id: int
    vehicle_class: str
    driver_rating: float
    registered_at: datetime

    def __post_init__(self) -> None:
        if self.driver_id <= 0:
            raise ValueError(f"Invalid driver_id: {self.driver_id}")
        if self.home_city_id <= 0:
            raise ValueError(f"Home City id must be positive")
        if not 1 <= self.driver_rating <= 5:
            raise ValueError("Driver rating must be between 1 and 5")


@dataclass(frozen=True, slots=True)
class City:
    city_id: int
    city_name: str
    tz_name: str
    traffic_factor: float
    demand_weight: float

    def __post_init__(self) -> None:
        if self.city_id <= 0:
            raise ValueError(f"Invalid city_id: {self.city_id}")
        if not self.city_name.strip():
            raise ValueError("City name must not be empty")
        if self.traffic_factor <= 0:
            raise ValueError("Traffic factor must be positive")
        if self.demand_weight <= 0:
            raise ValueError("Demand weight must be positive")


@dataclass(frozen=True, slots=True)
class Zone:
    zone_id: int
    city_id: int
    zone_name: str
    zone_type: ZoneType

    def __post_init__(self) -> None:
        if self.zone_id <= 0:
            raise ValueError(f"Invalid zone_id: {self.zone_id}")
        if not self.zone_name.strip():
            raise ValueError("Zone name must not be empty")
        if self.city_id <= 0:
            raise ValueError(f"Invalid city_id: {self.city_id}")


@dataclass(frozen=True, slots=True)
class ServiceTypeInfo:
    service_type_id: int
    service_name: str
    category: ServiceCategory
    base_fare: float
    per_km: float
    per_min: float

    def __post_init__(self) -> None:
        if not self.service_name.strip():
            raise ValueError("Service type name must not be empty")
        if self.base_fare <= 0:
            raise ValueError("Base fare must be positive")
        if self.per_km <= 0:
            raise ValueError("Per-km must be positive")
        if self.per_min <= 0:
            raise ValueError("Per-min must be positive")


@dataclass(frozen=True, slots=True)
class TripStatusInfo:
    status_id: int
    status_name: str

    def __post_init__(self) -> None:
        if self.status_id <= 0:
            raise ValueError(f"Invalid status_id: {self.status_id}")
        if not self.status_name.strip():
            raise ValueError("Status name must not be empty")


@dataclass(frozen=True, slots=True)
class Trip:
    trip_id: UUID
    started_at: datetime
    driver_id: int
    city_id: int
    pickup_zone_id: int
    dropoff_zone_id: int
    service_type_id: ServiceType
    status_id: TripStatus
    distance_km: float
    duration_min: float
    surge: float
    fare: float
    tip: float
    trip_rating: int
    is_anomaly: bool

    def __post_init__(self) -> None:
        if not 0 <= self.trip_rating <= 5:
            raise ValueError("Trip rating must be between 0 and 5")
        if self.city_id <= 0:
            raise ValueError("City id must be positive")
        if self.driver_id <= 0:
            raise ValueError("Driver id must be positive")
        if self.tip < 0:
            raise ValueError("Tip must be positive")
        if self.fare < 0:
            raise ValueError("Fare must be positive")
        if self.surge < 1:
            raise ValueError("Surge must be at least 1")
        if self.pickup_zone_id <= 0:
            raise ValueError("Pickup zone id must be positive")
        if self.dropoff_zone_id <= 0:
            raise ValueError("Dropoff zone id must be positive")
        if self.service_type_id <= 0:
            raise ValueError("Service type id must be positive")
        if self.distance_km <= 0:
            raise ValueError("Distance must be positive")
        if self.duration_min <= 0:
            raise ValueError("Duration min must be positive")
        if self.status_id != TripStatus.COMPLETED and (self.fare != 0 or self.tip != 0 or self.trip_rating != 0):
            raise ValueError("Only completed trips can have fare, tip or rating")
