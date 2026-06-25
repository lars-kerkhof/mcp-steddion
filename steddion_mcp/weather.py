"""Open-Meteo weather forecast integration."""

from __future__ import annotations

from datetime import date
from functools import lru_cache

import httpx

from .mock_data import mock_weather_forecast
from .models import HourWeather, WeatherForecast

_OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"


@lru_cache(maxsize=64)
def get_weather_forecast(latitude: float, longitude: float, target_date: date | None = None) -> WeatherForecast:
    if target_date is None:
        target_date = date.today()

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,wind_speed_10m,shortwave_radiation",
        "start_date": target_date.isoformat(),
        "end_date": target_date.isoformat(),
        "timezone": "UTC",
    }

    try:
        resp = httpx.get(_OPEN_METEO_BASE, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, Exception):
        return mock_weather_forecast(latitude, longitude, target_date)

    hourly_data = data.get("hourly", {})
    temps = hourly_data.get("temperature_2m", [])
    winds = hourly_data.get("wind_speed_10m", [])
    ghis = hourly_data.get("shortwave_radiation", [])

    if not temps:
        return mock_weather_forecast(latitude, longitude, target_date)

    hourly = []
    for h in range(min(24, len(temps))):
        hourly.append(HourWeather(
            hour=h,
            temperature_c=round(temps[h], 1),
            wind_speed_m_s=round(winds[h] / 3.6, 1) if h < len(winds) else 0.0,
            ghi_w_m2=round(ghis[h], 1) if h < len(ghis) else 0.0,
        ))

    return WeatherForecast(
        latitude=latitude,
        longitude=longitude,
        date=target_date,
        hourly=hourly,
        source="open_meteo",
    )
