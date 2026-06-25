"""BESS (Battery Energy Storage System) business case calculator."""

from __future__ import annotations

from datetime import date

from .entsoe import get_day_ahead_prices
from .models import BessAssumption, BessBusinessCase, ChargeDischargePlan


def calculate_bess_business_case(
    power_mw: float,
    energy_mwh: float,
    target_date: date,
    round_trip_efficiency: float = 0.85,
) -> BessBusinessCase:
    da = get_day_ahead_prices(target_date)

    hours_per_cycle = energy_mwh / power_mw if power_mw > 0 else float("inf")
    charge_hours = int(hours_per_cycle)
    discharge_hours = int(hours_per_cycle)

    if charge_hours < 1 or discharge_hours < 1:
        raise ValueError("Power/energy ratio results in sub-hourly cycles, which is not supported.")

    sorted_by_price = sorted(da.prices, key=lambda p: p.price_eur_mwh)
    cheapest = sorted_by_price[:charge_hours]
    most_expensive = sorted_by_price[-discharge_hours:]

    charge_set = {p.hour for p in cheapest}
    discharge_set = {p.hour for p in most_expensive}
    overlap = charge_set & discharge_set
    if overlap:
        discharge_set -= overlap
        most_expensive = [p for p in most_expensive if p.hour not in overlap]

    if not most_expensive:
        avg_charge = sum(p.price_eur_mwh for p in cheapest) / len(cheapest) if cheapest else 0
        return BessBusinessCase(
            date=target_date,
            power_mw=power_mw,
            energy_mwh=energy_mwh,
            round_trip_efficiency=round_trip_efficiency,
            estimated_revenue_eur=0,
            cycles_used=0,
            spread_eur_mwh=0,
            schedule=[],
            assumptions=_assumptions(round_trip_efficiency),
            source="mock" if da.source == "mock" else "calculated",
        )

    charge_cost = sum(p.price_eur_mwh for p in cheapest) * power_mw
    discharge_revenue = sum(p.price_eur_mwh for p in most_expensive) * power_mw * round_trip_efficiency
    net_revenue = discharge_revenue - charge_cost

    avg_charge_price = sum(p.price_eur_mwh for p in cheapest) / len(cheapest)
    avg_discharge_price = sum(p.price_eur_mwh for p in most_expensive) / len(most_expensive)

    schedule: list[ChargeDischargePlan] = []
    for hp in da.prices:
        if hp.hour in charge_set:
            schedule.append(ChargeDischargePlan(
                hour=hp.hour, action="charge", power_mw=power_mw, price_eur_mwh=hp.price_eur_mwh,
            ))
        elif hp.hour in discharge_set:
            schedule.append(ChargeDischargePlan(
                hour=hp.hour, action="discharge",
                power_mw=round(power_mw * round_trip_efficiency, 2),
                price_eur_mwh=hp.price_eur_mwh,
            ))
        else:
            schedule.append(ChargeDischargePlan(
                hour=hp.hour, action="idle", power_mw=0, price_eur_mwh=hp.price_eur_mwh,
            ))

    cycles = min(len(cheapest), len(most_expensive)) / hours_per_cycle if hours_per_cycle > 0 else 0

    return BessBusinessCase(
        date=target_date,
        power_mw=power_mw,
        energy_mwh=energy_mwh,
        round_trip_efficiency=round_trip_efficiency,
        estimated_revenue_eur=round(net_revenue, 2),
        cycles_used=round(cycles, 2),
        spread_eur_mwh=round(avg_discharge_price - avg_charge_price, 2),
        schedule=schedule,
        assumptions=_assumptions(round_trip_efficiency),
        source="mock" if da.source == "mock" else "calculated",
    )


def _assumptions(rte: float) -> list[BessAssumption]:
    return [
        BessAssumption(name="Strategy", value="Day-ahead price arbitrage (buy low, sell high)"),
        BessAssumption(name="Round-trip efficiency", value=f"{rte:.0%}"),
        BessAssumption(name="Degradation", value="Not modelled"),
        BessAssumption(name="Grid fees & taxes", value="Not included"),
        BessAssumption(name="Ancillary services", value="Not included (FCR/aFRR revenue stacking excluded)"),
        BessAssumption(name="Intraday trading", value="Not included"),
    ]
