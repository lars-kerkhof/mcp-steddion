"""Tests for BESS business case calculator using mock data."""

import os
from datetime import date

from steddion_mcp.bess import calculate_bess_business_case


def test_bess_returns_schedule():
    os.environ.pop("ENTSOE_API_TOKEN", None)
    result = calculate_bess_business_case(10.0, 40.0, date(2025, 1, 15))
    assert result.source == "mock"
    assert len(result.schedule) == 24
    assert result.estimated_revenue_eur != 0
    assert result.power_mw == 10.0
    assert result.energy_mwh == 40.0


def test_bess_efficiency_applied():
    os.environ.pop("ENTSOE_API_TOKEN", None)
    result_85 = calculate_bess_business_case(10.0, 40.0, date(2025, 1, 15), 0.85)
    result_95 = calculate_bess_business_case(10.0, 40.0, date(2025, 1, 15), 0.95)
    assert result_95.estimated_revenue_eur > result_85.estimated_revenue_eur


def test_bess_assumptions_present():
    os.environ.pop("ENTSOE_API_TOKEN", None)
    result = calculate_bess_business_case(5.0, 10.0, date(2025, 6, 1))
    assert len(result.assumptions) > 0
    names = [a.name for a in result.assumptions]
    assert "Round-trip efficiency" in names


def test_bess_has_charge_and_discharge():
    os.environ.pop("ENTSOE_API_TOKEN", None)
    result = calculate_bess_business_case(10.0, 20.0, date(2025, 3, 10))
    actions = {s.action for s in result.schedule}
    assert "charge" in actions
    assert "discharge" in actions
