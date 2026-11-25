import random
from datetime import datetime, timedelta
from generator.models import Driver
from generator.generation.catalog import CityCatalog

FIRST_NAMES = [
    "Alexander", "Dmitry", "Ivan", "Mikhail", "Artem",
    "Maxim", "Nikita", "Kirill", "Ilya", "Roman",
    "Vladislav", "Timur", "Yaroslav", "Matvey", "Denis",
    "Alexey", "Andrey", "Sergey", "Egor", "Pavel",
    "Anastasia", "Maria", "Anna", "Ekaterina", "Sofia",
    "Daria", "Polina", "Alina", "Victoria", "Elena",
]

LAST_NAMES = [
    "Ivanov", "Smirnov", "Kuznetsov", "Popov", "Sokolov",
    "Lebedev", "Kozlov", "Novikov", "Morozov", "Petrov",
    "Volkov", "Solovyov", "Vasiliev", "Zaitsev", "Pavlov",
    "Semenov", "Golubev", "Vinogradov", "Bogdanov", "Vorobyov",
    "Fedorov", "Mikhailov", "Belov", "Orlov", "Komarov",
    "Romanova", "Sokolova", "Kuznetsova", "Morozova", "Petrova",
]

VEHICLE_CLASSES = ["economy", "comfort", "delivery"]
VEHICLE_WEIGHTS = [60, 25, 15]

def generate_drivers(
    count: int,
    catalog: CityCatalog,
    rng: random.Random,
    now: datetime,
) -> list[Driver]:
    if count <= 0:
        raise ValueError("Count must be greater than 0")

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Datetime must be timezone-aware")

    drivers: list[Driver] = []
    five_years = timedelta(days=5 * 365)
    for driver_id in range(1, count + 1):
        # Выбираем случайный город с учетом спроса
        city = catalog.pick_city(rng)

        # Генерируем случайное имя и фамилию
        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"

        # Выбираем класс автомобиля с заданными вероятностями
        vehicle_class = rng.choices(
            VEHICLE_CLASSES,
            weights=VEHICLE_WEIGHTS,
            k=1,
        )[0]

        # Генерируем рейтинг
        driver_rating = rng.gauss(4.7, 0.25)
        driver_rating = max(3.5, min(driver_rating, 5.0))
        driver_rating = round(driver_rating, 2)

        # Генерируем дату регистрации за последние 5 лет
        random_seconds = rng.uniform(
            0,
            five_years.total_seconds(),
        )
        registered_at = now - timedelta(seconds=random_seconds)
        driver = Driver(
            driver_id=driver_id,
            full_name=full_name,
            home_city_id=city.city_id,
            vehicle_class=vehicle_class,
            driver_rating=driver_rating,
            registered_at=registered_at,
        )
        drivers.append(driver)
    return drivers
