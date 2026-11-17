from datetime import datetime
from zoneinfo import ZoneInfo
import math

def local_hour(dt_utc: datetime, tz_name: str) -> float:
    """Return local time as fractional hour."""
    if dt_utc.tzinfo is None or dt_utc.utcoffset() is None:
        raise ValueError("dt_utc must be timezone-aware")

    local_dt = dt_utc.astimezone(ZoneInfo(tz_name))
    return (
        local_dt.hour
        + local_dt.minute / 60
        + local_dt.second / 3600
        + local_dt.microsecond / 3600000000
    )

def demand_multiplier(dt_utc: datetime, tz_name: str) -> float:
    """Calculate demand multiplier based on local time and weekday."""
    hour = local_hour(dt_utc, tz_name)
    local_dt = dt_utc.astimezone(ZoneInfo(tz_name))
    weekday = local_dt.weekday()

    # Base demand: demand never reaches zero.
    demand = 0.25

    # Morning peak around 08:30.
    morning_peak = math.exp (
        -((hour - 8.5) ** 2) / (2 * 1.5 ** 2)
    )

    #Evening peak around 18:30.
    evening_peak = math.exp (
        -((hour - 18.5) ** 2) / (2 * 1.5 ** 2)
    )

    # Add daily demand peaks.
    demand += 0.65 * morning_peak
    demand += 1.0 * evening_peak

    # Friday and Saturday evenings are busier.
    if weekday in (4, 5):
        demand += 0.35 * evening_peak

    # Sunday mornings are quieter.
    if weekday == 6:
        demand -= 0.25 * morning_peak

    return demand