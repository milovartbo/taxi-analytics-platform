import random
from zoneinfo import ZoneInfo
from generator.models import (
    City,
    ServiceCategory,
    ServiceType,
    ServiceTypeInfo,
    Zone,
    ZoneType
)

_ZoneTemplate = tuple[str, ZoneType]

_CityTemplate = tuple[
    int,
    str,
    float,
    float,
    tuple[_ZoneTemplate, ...]
]

_CITY_TEMPLATES: dict[str, _CityTemplate] = {
    "Vladivostok": (
        1,
        "Asia/Vladivostok",
        1.2,
        1.0,
        (
            ("Leninsky District", ZoneType.CENTER),
            ("Pervomaysky District", ZoneType.RESIDENTIAL),
            ("Pervorechensky District", ZoneType.RESIDENTIAL),
            ("Sovetsky District", ZoneType.RESIDENTIAL),
            ("Knevichi Airport", ZoneType.AIRPORT)
        ),
    ),
    "Moscow": (
        2,
        "Europe/Moscow",
        1.4,
        3.0,
        (
            ("Tverskoy District", ZoneType.CENTER),
            ("Arbat District", ZoneType.CENTER),
            ("Presnensky District", ZoneType.RESIDENTIAL),
            ("Khamovniki District", ZoneType.RESIDENTIAL),
            ("Sheremetyevo Airport", ZoneType.AIRPORT),
            ("ZIL Industrial Zone", ZoneType.INDUSTRIAL)
        ),
    ),
    "Novosibirsk": (
        3,
        "Asia/Novosibirsk",
        1.2,
        1.2,
        (
            ("Centralny District", ZoneType.CENTER),
            ("Zheleznodorozhny District", ZoneType.RESIDENTIAL),
            ("Oktyabrsky District", ZoneType.RESIDENTIAL),
            ("Leninsky District", ZoneType.RESIDENTIAL),
            ("Tolmachevo Airport", ZoneType.AIRPORT)
        ),
    ),
    "Kazan": (
        4,
        "Europe/Moscow",
        1.1,
        0.9,
        (
            ("Vakhitovsky District", ZoneType.CENTER),
            ("Novo-Savinovsky District", ZoneType.RESIDENTIAL),
            ("Privolzhsky District", ZoneType.RESIDENTIAL),
            ("Sovetsky District", ZoneType.RESIDENTIAL),
            ("Kazan International Airport", ZoneType.AIRPORT)
        ),
    ),
    "Yekaterinburg": (
        5,
        "Asia/Yekaterinburg",
        1.3,
        1.0,
        (
            ("Leninsky District", ZoneType.CENTER),
            ("Verkh-Isetsky District", ZoneType.RESIDENTIAL),
            ("Kirovsky District", ZoneType.RESIDENTIAL),
            ("Oktyabrsky District", ZoneType.RESIDENTIAL),
            ("Koltsovo Airport", ZoneType.AIRPORT)
        ),
    ),
}


_SERVICE_TYPES: tuple[ServiceTypeInfo, ...] = (
    ServiceTypeInfo(
        service_type_id=ServiceType.ECONOMY,
        service_name="economy",
        category=ServiceCategory.PASSENGER,
        base_fare=100.0,
        per_km=30.0,
        per_min=8.0
    ),
    ServiceTypeInfo(
        service_type_id=ServiceType.COMFORT,
        service_name="comfort",
        category=ServiceCategory.PASSENGER,
        base_fare=150.0,
        per_km=40.0,
        per_min=12.0
    ),
    ServiceTypeInfo(
        service_type_id=ServiceType.DELIVERY,
        service_name="delivery",
        category=ServiceCategory.DELIVERY,
        base_fare=80.0,
        per_km=22.0,
        per_min=6.0
    ),
)

class CityCatalog:
    """Каталог городов и районов для генерации поездок."""
    def __init__(self, city_names: list[str]) -> None:
        self._cities: list[City] = []
        self._zones: list[Zone] = []
        self._zones_by_city: dict[int, list[Zone]] = {}

        if not city_names:
            raise ValueError("City list must not be empty")

        for city_name in dict.fromkeys(city_names):
            template = _CITY_TEMPLATES.get(city_name)

            if template is None:
                raise ValueError(f"Unknown city: {city_name}")

            city_id, tz_name, traffic_factor, demand_weight, zone_templates = template
            ZoneInfo(tz_name)
            city = City(
                city_id=city_id,
                city_name=city_name,
                tz_name=tz_name,
                traffic_factor=traffic_factor,
                demand_weight=demand_weight
            )

            self._cities.append(city)
            city_zones = [
                Zone(
                    zone_id=city_id * 100 + index,
                    city_id=city_id,
                    zone_name=zone_name,
                    zone_type=zone_type
                )
                for index, (zone_name, zone_type) in enumerate(
                    zone_templates,
                    start=1
                )
            ]

            self._zones.extend(city_zones)
            self._zones_by_city[city_id] = city_zones

    def cities(self) -> list[City]:
        """Возвращает выбранные города."""
        return self._cities.copy()

    def zones(self) -> list[Zone]:
        """Возвращает районы всех выбранных городов."""
        return self._zones.copy()

    def zones_of(self, city_id: int) -> list[Zone]:
        """Возвращает районы указанного города."""
        return self._zones_by_city.get(city_id, []).copy()

    def pick_city(self, rng: random.Random) -> City:
        """Выбирает город с учетом веса спроса."""
        return rng.choices(
            self._cities,
            weights=[city.demand_weight for city in self._cities],
            k=1
        )[0]

    def pick_zones(
        self,
        city_id: int,
        rng: random.Random,
    ) -> tuple[int, int]:
        """Выбирает районы отправления и назначения одного города."""
        city_zones = self.zones_of(city_id)

        if len(city_zones) < 2:
            raise ValueError(f"City {city_id} must have at least 2 zones")

        pickup = rng.choice(city_zones)

        if rng.random() < 0.15:
            return pickup.zone_id, pickup.zone_id

        dropoff_candidates = [
            zone for zone in city_zones
            if zone.zone_id != pickup.zone_id
        ]

        dropoff = rng.choice(dropoff_candidates)

        return pickup.zone_id, dropoff.zone_id


def service_types() -> list[ServiceTypeInfo]:
    """Возвращает доступные типы сервиса."""
    return list(_SERVICE_TYPES)
