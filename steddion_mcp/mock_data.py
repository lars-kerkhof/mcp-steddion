"""Realistic mock data generators for when API credentials are unavailable."""

from __future__ import annotations

import math
import random
from datetime import date, datetime, timezone

from .models import (
    DayAheadPrices,
    HourPrice,
    HourWeather,
    ImbalancePrices,
    ImbalanceRecord,
    WeatherForecast,
)

_TYPICAL_NL_PRICES = [
    38, 35, 32, 30, 29, 31, 45, 68,
    85, 92, 88, 78, 72, 70, 65, 60,
    58, 72, 95, 110, 105, 88, 62, 45,
]


def mock_day_ahead_prices(target_date: date, bidding_zone: str) -> DayAheadPrices:
    seed = target_date.toordinal()
    rng = random.Random(seed)

    prices = []
    for h, base in enumerate(_TYPICAL_NL_PRICES):
        noise = rng.gauss(0, 8)
        prices.append(HourPrice(hour=h, price_eur_mwh=round(base + noise, 2)))

    peak = [p.price_eur_mwh for p in prices if 8 <= p.hour < 20]
    off_peak = [p.price_eur_mwh for p in prices if p.hour < 8 or p.hour >= 20]
    all_p = [p.price_eur_mwh for p in prices]

    return DayAheadPrices(
        date=target_date,
        bidding_zone=bidding_zone,
        prices=prices,
        peak_avg_eur_mwh=round(sum(peak) / len(peak), 2),
        off_peak_avg_eur_mwh=round(sum(off_peak) / len(off_peak), 2),
        spread_eur_mwh=round(max(all_p) - min(all_p), 2),
        source="mock",
    )


def mock_imbalance_prices(target_date: date) -> ImbalancePrices:
    seed = target_date.toordinal() + 1000
    rng = random.Random(seed)

    records = []
    for quarter in range(96):
        h = quarter // 4
        base = _TYPICAL_NL_PRICES[h]
        up = base + abs(rng.gauss(15, 10))
        down = base - abs(rng.gauss(10, 8))
        ts = datetime(target_date.year, target_date.month, target_date.day,
                      h, (quarter % 4) * 15, tzinfo=timezone.utc)
        records.append(ImbalanceRecord(
            timestamp=ts,
            price_up_eur_mwh=round(up, 2),
            price_down_eur_mwh=round(max(0, down), 2),
        ))

    return ImbalancePrices(date=target_date, records=records, source="mock")


def mock_weather_forecast(latitude: float, longitude: float, target_date: date) -> WeatherForecast:
    seed = target_date.toordinal() + int(latitude * 100) + int(longitude * 100)
    rng = random.Random(seed)

    day_of_year = target_date.timetuple().tm_yday
    hourly = []
    for h in range(24):
        temp_base = 10 + 8 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
        temp = temp_base + 3 * math.sin(math.pi * (h - 6) / 12) + rng.gauss(0, 1.5)

        sunrise, sunset = 6, 20
        if sunrise <= h <= sunset:
            solar_angle = math.sin(math.pi * (h - sunrise) / (sunset - sunrise))
            ghi = max(0, 800 * solar_angle * (0.5 + 0.5 * rng.random()))
        else:
            ghi = 0.0

        wind = max(0, 5 + rng.gauss(0, 3))

        hourly.append(HourWeather(
            hour=h,
            temperature_c=round(temp, 1),
            wind_speed_m_s=round(wind, 1),
            ghi_w_m2=round(ghi, 1),
        ))

    return WeatherForecast(
        latitude=latitude,
        longitude=longitude,
        date=target_date,
        hourly=hourly,
        source="mock",
    )
