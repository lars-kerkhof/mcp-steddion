"""Tests that run against the mock data layer — no network calls."""

from datetime import date

from steddion_mcp.mock_data import (
    mock_day_ahead_prices,
    mock_imbalance_prices,
    mock_weather_forecast,
)


def test_day_ahead_prices_returns_24_hours():
    result = mock_day_ahead_prices(date(2025, 1, 15), "NL")
    assert len(result.prices) == 24
    assert result.source == "mock"
    assert result.bidding_zone == "NL"


def test_day_ahead_prices_deterministic():
    a = mock_day_ahead_prices(date(2025, 6, 1), "NL")
    b = mock_day_ahead_prices(date(2025, 6, 1), "NL")
    assert a.prices == b.prices


def test_day_ahead_peak_off_peak():
    result = mock_day_ahead_prices(date(2025, 3, 10), "NL")
    peak = [p.price_eur_mwh for p in result.prices if 8 <= p.hour < 20]
    off_peak = [p.price_eur_mwh for p in result.prices if p.hour < 8 or p.hour >= 20]
    assert abs(result.peak_avg_eur_mwh - sum(peak) / len(peak)) < 0.01
    assert abs(result.off_peak_avg_eur_mwh - sum(off_peak) / len(off_peak)) < 0.01


def test_day_ahead_spread():
    result = mock_day_ahead_prices(date(2025, 3, 10), "NL")
    all_p = [p.price_eur_mwh for p in result.prices]
    assert abs(result.spread_eur_mwh - (max(all_p) - min(all_p))) < 0.01


def test_imbalance_prices_returns_96_records():
    result = mock_imbalance_prices(date(2025, 1, 15))
    assert len(result.records) == 96
    assert result.source == "mock"


def test_imbalance_up_greater_than_down():
    result = mock_imbalance_prices(date(2025, 1, 15))
    for r in result.records:
        assert r.price_up_eur_mwh >= r.price_down_eur_mwh


def test_weather_forecast_returns_24_hours():
    result = mock_weather_forecast(52.37, 4.90, date(2025, 7, 1))
    assert len(result.hourly) == 24
    assert result.source == "mock"


def test_weather_no_solar_at_night():
    result = mock_weather_forecast(52.37, 4.90, date(2025, 7, 1))
    for h in result.hourly:
        if h.hour < 6 or h.hour > 20:
            assert h.ghi_w_m2 == 0.0
