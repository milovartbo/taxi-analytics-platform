from datetime import datetime
from zoneinfo import ZoneInfo
import math

def local_hour(dt_utc: datetime, tz_name: str) -> float:
    """Возвращает местное время в виде дробного числа часов."""
    if dt_utc.tzinfo is None or dt_utc.utcoffset() is None:
        raise ValueError("dt_utc must be timezone-aware")

    local_dt = dt_utc.astimezone(ZoneInfo(tz_name))
    return (
        local_dt.hour
        + local_dt.minute / 60.0
        + local_dt.second / 3600.0
        + local_dt.microsecond / 3600000000.0
    )

def demand_multiplier(dt_utc: datetime, tz_name: str) -> float:
    """Рассчитывает множитель спроса на основе местного времени и дня недели"""
    if dt_utc.tzinfo is None or dt_utc.utcoffset() is None:
        raise ValueError("dt_utc must be timezone-aware")

    local_dt = dt_utc.astimezone(ZoneInfo(tz_name))
    hour = local_hour(dt_utc, tz_name)
    weekday = local_dt.weekday()

    #Суточный цикл спроса: максимум около 15:00, минимум 03:00.
    daily_factor = math.cos( 2.0 * math.pi * (hour - 15.0) / 24.0)

    # Базовый уровень с учётом косинусоиды
    demand = 0.5 + 0.2 * daily_factor

    # Утренний пик около 08:30
    morning_factor = math.exp(-((hour - 8.5) ** 2) / (2.0 * 1.5 ** 2))

    # Вечерний пик около 18:30
    evening_factor = math.exp(-((hour - 18.5) ** 2) / (2.0 * 1.5 ** 2))

    # Добавляем два пика
    demand += 0.3 * morning_factor
    demand += 0.6 * evening_factor

    # Пятница и суббота
    if weekday in (4, 5):
        demand += 0.2 * evening_factor

    # Воскресенье
    if weekday == 6:
        demand -= 0.15 * morning_factor

    return max(demand, 0.01)