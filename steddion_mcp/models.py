from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, Field


class HourPrice(BaseModel):
    hour: int = Field(description="Hour of the day (0-23, or 0-24 during DST transitions)")
    price_eur_mwh: float = Field(description="Day-ahead price in EUR/MWh")


class DayAheadPrices(BaseModel):
    date: date
    bidding_zone: str
    currency: str = "EUR"
    unit: str = "MWh"
    prices: list[HourPrice]
    peak_avg_eur_mwh: float = Field(description="Average price during peak hours (08:00-20:00)")
    off_peak_avg_eur_mwh: float = Field(description="Average price during off-peak hours")
    spread_eur_mwh: float = Field(description="Difference between max and min hourly price")
    source: str = Field(description="'entsoe' for live data, 'mock' for simulated data")


class ImbalanceRecord(BaseModel):
    timestamp: datetime = Field(description="Start of the imbalance settlement period (UTC)")
    price_up_eur_mwh: float = Field(description="Upward regulation price (shortage) in EUR/MWh")
    price_down_eur_mwh: float = Field(description="Downward regulation price (surplus) in EUR/MWh")


class ImbalancePrices(BaseModel):
    date: date
    records: list[ImbalanceRecord]
    source: str = Field(description="'tennet' for live data, 'mock' for simulated data")


class HourWeather(BaseModel):
    hour: int
    temperature_c: float = Field(description="Temperature in degrees Celsius")
    wind_speed_m_s: float = Field(description="Wind speed at 10m in m/s")
    ghi_w_m2: float = Field(description="Global Horizontal Irradiance in W/m2")


class WeatherForecast(BaseModel):
    latitude: float
    longitude: float
    date: date
    hourly: list[HourWeather]
    source: str = Field(description="'open_meteo' for live data, 'mock' for simulated data")


class BessAssumption(BaseModel):
    name: str
    value: str


class ChargeDischargePlan(BaseModel):
    hour: int
    action: str = Field(description="'charge', 'discharge', or 'idle'")
    power_mw: float
    price_eur_mwh: float


class BessBusinessCase(BaseModel):
    date: date
    power_mw: float
    energy_mwh: float
    round_trip_efficiency: float
    estimated_revenue_eur: float = Field(description="Estimated net revenue from day-ahead arbitrage")
    cycles_used: float = Field(description="Number of full charge/discharge cycles used")
    spread_eur_mwh: float = Field(description="Price spread captured (avg discharge price - avg charge price)")
    schedule: list[ChargeDischargePlan] = Field(description="Hourly charge/discharge schedule")
    assumptions: list[BessAssumption]
    source: str = Field(description="'calculated' using live prices, 'mock' using simulated prices")
