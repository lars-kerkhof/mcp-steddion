"""ENTSO-E Transparency Platform integration for day-ahead prices."""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
from functools import lru_cache

import httpx

from .mock_data import mock_day_ahead_prices
from .models import DayAheadPrices, HourPrice

_ENTSOE_BASE = "https://web-api.tp.entsoe.eu/api"

_ZONE_MAP = {
    "NL": "10YNL----------L",
    "DE": "10Y1001A1001A82H",
    "BE": "10YBE----------2",
    "FR": "10YFR-RTE------C",
}


@lru_cache(maxsize=64)
def get_day_ahead_prices(target_date: date, bidding_zone: str = "NL") -> DayAheadPrices:
    token = os.environ.get("ENTSOE_API_TOKEN", "").strip()
    if not token:
        return mock_day_ahead_prices(target_date, bidding_zone)

    area_code = _ZONE_MAP.get(bidding_zone.upper())
    if not area_code:
        raise ValueError(
            f"Unknown bidding zone '{bidding_zone}'. Supported: {', '.join(_ZONE_MAP)}"
        )

    period_start = datetime(target_date.year, target_date.month, target_date.day,
                            tzinfo=timezone.utc).strftime("%Y%m%d%H%M")
    period_end = datetime(target_date.year, target_date.month, target_date.day, 23, 59,
                          tzinfo=timezone.utc).strftime("%Y%m%d%H%M")

    params = {
        "securityToken": token,
        "documentType": "A44",
        "in_Domain": area_code,
        "out_Domain": area_code,
        "periodStart": period_start,
        "periodEnd": period_end,
    }

    try:
        resp = httpx.get(_ENTSOE_BASE, params=params, timeout=30)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"ENTSO-E API request failed: {exc}") from exc

    prices = _parse_entsoe_xml(resp.text, target_date)

    peak = [p.price_eur_mwh for p in prices if 8 <= p.hour < 20]
    off_peak = [p.price_eur_mwh for p in prices if p.hour < 8 or p.hour >= 20]
    all_p = [p.price_eur_mwh for p in prices]

    return DayAheadPrices(
        date=target_date,
        bidding_zone=bidding_zone,
        prices=prices,
        peak_avg_eur_mwh=round(sum(peak) / len(peak), 2) if peak else 0,
        off_peak_avg_eur_mwh=round(sum(off_peak) / len(off_peak), 2) if off_peak else 0,
        spread_eur_mwh=round(max(all_p) - min(all_p), 2) if all_p else 0,
        source="entsoe",
    )


def _parse_entsoe_xml(xml_text: str, target_date: date) -> list[HourPrice]:
    import xml.etree.ElementTree as ET

    ns = {"ns": "urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3"}
    root = ET.fromstring(xml_text)

    prices: list[HourPrice] = []
    for ts in root.findall(".//ns:TimeSeries", ns):
        for period in ts.findall("ns:Period", ns):
            for point in period.findall("ns:Point", ns):
                pos = int(point.find("ns:position", ns).text)
                price = float(point.find("ns:price.amount", ns).text)
                prices.append(HourPrice(hour=pos - 1, price_eur_mwh=round(price, 2)))

    prices.sort(key=lambda p: p.hour)
    return prices
