"""TenneT imbalance price integration."""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
from functools import lru_cache

import httpx

from .mock_data import mock_imbalance_prices
from .models import ImbalancePrices, ImbalanceRecord

_TENNET_BASE = "https://api.tennet.eu/balancedelta/v1/balancedeltaprices"


@lru_cache(maxsize=64)
def get_imbalance_prices(target_date: date) -> ImbalancePrices:
    try:
        resp = httpx.get(
            _TENNET_BASE,
            params={"startDate": target_date.isoformat(), "endDate": target_date.isoformat()},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, Exception):
        return mock_imbalance_prices(target_date)

    if not data:
        return mock_imbalance_prices(target_date)

    records = []
    for entry in data:
        try:
            ts = datetime.fromisoformat(entry["startTime"])
            records.append(ImbalanceRecord(
                timestamp=ts,
                price_up_eur_mwh=round(float(entry.get("upwardIncidentalPrice", 0)), 2),
                price_down_eur_mwh=round(float(entry.get("downwardIncidentalPrice", 0)), 2),
            ))
        except (KeyError, ValueError):
            continue

    if not records:
        return mock_imbalance_prices(target_date)

    records.sort(key=lambda r: r.timestamp)
    return ImbalancePrices(date=target_date, records=records, source="tennet")
