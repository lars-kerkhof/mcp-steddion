"""Steddion Energy MCP Server – main entry point."""

from __future__ import annotations

import os
from datetime import date

from dotenv import load_dotenv
from fastmcp import FastMCP

from . import bess as bess_mod
from . import entsoe as entsoe_mod
from . import tennet as tennet_mod
from . import weather as weather_mod
from .models import BessBusinessCase, DayAheadPrices, ImbalancePrices, WeatherForecast

load_dotenv()

INSTRUCTIONS = (
    "Steddion Energy MCP Server – tools for Dutch energy market analysis and BESS feasibility.\n\n"
    "Available tools:\n"
    "• get_day_ahead_prices – hourly electricity prices from ENTSO-E. Start here to understand market conditions.\n"
    "• get_imbalance_prices – TenneT real-time imbalance prices, useful for balancing risk analysis.\n"
    "• get_weather_forecast – wind, solar irradiance & temperature for a location; combine with prices for renewable forecasting.\n"
    "• calculate_bess_business_case – estimate battery storage arbitrage revenue for a given day.\n\n"
    "Typical workflow: fetch day-ahead prices first, then run the BESS business case for the same date. "
    "Add weather data to assess solar/wind correlation with price patterns. "
    "All tools return structured data with a 'source' field indicating whether live or mock data was used."
)

mcp = FastMCP(
    "Steddion Energy",
    instructions=INSTRUCTIONS,
)


@mcp.tool(
    annotations={"readOnlyHint": True},
)
def get_day_ahead_prices(
    date: date,
    bidding_zone: str = "NL",
) -> DayAheadPrices:
    """Use this when you need hourly day-ahead electricity prices for a specific date and bidding zone.

    Returns the full price curve (EUR/MWh) plus peak/off-peak averages and the daily spread.
    Supported bidding zones: NL, DE, BE, FR.

    Args:
        date: The delivery date to fetch prices for (format: YYYY-MM-DD).
        bidding_zone: European bidding zone code. Defaults to "NL" (Netherlands).
    """
    return entsoe_mod.get_day_ahead_prices(date, bidding_zone)


@mcp.tool(
    annotations={"readOnlyHint": True},
)
def get_imbalance_prices(
    date: date,
) -> ImbalancePrices:
    """Use this when you need Dutch electricity imbalance (onbalans) prices for a specific date.

    Returns quarter-hourly upward and downward regulation prices from TenneT.

    Args:
        date: The date to fetch imbalance prices for (format: YYYY-MM-DD).
    """
    return tennet_mod.get_imbalance_prices(date)


@mcp.tool(
    annotations={"readOnlyHint": True},
)
def get_weather_forecast(
    latitude: float,
    longitude: float,
) -> WeatherForecast:
    """Use this when you need a weather forecast (wind speed, solar irradiance, temperature) for an energy-related analysis.

    Returns today's hourly forecast via Open-Meteo. No API key required.
    Common coordinates: Amsterdam (52.37, 4.90), Rotterdam (51.92, 4.48), Groningen (53.22, 6.57).

    Args:
        latitude: Location latitude in decimal degrees (e.g. 52.37 for Amsterdam).
        longitude: Location longitude in decimal degrees (e.g. 4.90 for Amsterdam).
    """
    return weather_mod.get_weather_forecast(latitude, longitude)


@mcp.tool(
    annotations={"readOnlyHint": True},
)
def calculate_bess_business_case(
    power_mw: float,
    energy_mwh: float,
    date: date,
    round_trip_efficiency: float = 0.85,
) -> BessBusinessCase:
    """Use this when you want to estimate the day-ahead arbitrage revenue for a battery energy storage system (BESS).

    Calculates optimal charge/discharge schedule by buying in cheapest hours and selling in most expensive hours,
    constrained by power rating, energy capacity, and round-trip efficiency.

    Args:
        power_mw: Battery power rating in MW (e.g. 10.0 for a 10 MW system).
        energy_mwh: Battery energy capacity in MWh (e.g. 40.0 for a 4-hour system).
        date: The date to run the business case for (uses day-ahead prices for this date).
        round_trip_efficiency: Round-trip efficiency as a fraction (default 0.85 = 85%).
    """
    return bess_mod.calculate_bess_business_case(power_mw, energy_mwh, date, round_trip_efficiency)


def main():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    mcp.run(transport="streamable-http", host=host, port=port)


if __name__ == "__main__":
    main()
