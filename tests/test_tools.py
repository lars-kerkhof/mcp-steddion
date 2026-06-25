"""Tests for the MCP tool wrappers in server.py."""

import os
from datetime import date

from steddion_mcp.server import (
    calculate_bess_business_case,
    get_day_ahead_prices,
    get_imbalance_prices,
    get_weather_forecast,
)


def setup_function():
    os.environ.pop("ENTSOE_API_TOKEN", None)


def test_get_day_ahead_prices_tool():
    result = get_day_ahead_prices(date(2025, 4, 1), "NL")
    assert result.source == "mock"
    assert len(result.prices) == 24


def test_get_imbalance_prices_tool():
    result = get_imbalance_prices(date(2025, 4, 1))
    assert result.source in ("mock", "tennet")
    assert len(result.records) >= 1


def test_get_weather_forecast_tool():
    result = get_weather_forecast(52.37, 4.90)
    assert result.source in ("mock", "open_meteo")
    assert len(result.hourly) == 24


def test_calculate_bess_business_case_tool():
    result = calculate_bess_business_case(10.0, 40.0, date(2025, 4, 1))
    assert result.source == "mock"
    assert result.estimated_revenue_eur != 0
