"""Linked three-statement forecast from calibrated historical base."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import numpy as np
import pandas as pd


def calibrate_drivers(hist: pd.DataFrame, drivers: dict[str, Any]) -> dict[str, Any]:
    """Anchor forecast drivers to latest actual year where sensible."""
    d = deepcopy(drivers)
    if hist.empty:
        return d
    last = hist.iloc[-1]
    rev = last.get("revenue")
    if rev and rev > 0:
        if last.get("gross_profit") is not None:
            gm = last["gross_profit"] / rev
            d["gross_margin"][0] = float(np.clip(gm, 0.35, 0.45))
        if len(hist) >= 2:
            prev_rev = hist.iloc[-2]["revenue"]
            if prev_rev and prev_rev > 0:
                g = rev / prev_rev - 1
                d["revenue_growth"][0] = float(np.clip(g, -0.05, 0.15))
    return d


def build_forecast(
    hist: pd.DataFrame,
    drivers: dict[str, Any],
    years: int,
    start_year: int,
) -> pd.DataFrame:
    if hist.empty:
        raise ValueError("Historical financials required to seed forecast.")

    last = hist.iloc[-1]
    base_rev = float(last["revenue"])
    base_year = int(last["fiscal_year"])

    forecast_years = list(range(start_year, start_year + years))
    if forecast_years[0] <= base_year:
        # Start forecast year after last reported actual
        forecast_years = list(range(base_year + 1, base_year + 1 + years))

    rows = []
    prev_rev = base_rev
    prev_nwc = base_rev * drivers.get("nwc_pct_revenue", 0.18)
    cash = float(last.get("cash") or 0)
    debt = float(last.get("total_debt") or 0)
    equity = float(last.get("equity") or 0)

    for i, fy in enumerate(forecast_years):
        g = drivers["revenue_growth"][min(i, len(drivers["revenue_growth"]) - 1)]
        revenue = prev_rev * (1 + g)
        gm = drivers["gross_margin"][min(i, len(drivers["gross_margin"]) - 1)]
        gross_profit = revenue * gm
        cogs = revenue - gross_profit
        sga = revenue * drivers["sg_a_pct_revenue"][min(i, len(drivers["sg_a_pct_revenue"]) - 1)]
        rd = revenue * drivers["rd_pct_revenue"][min(i, len(drivers["rd_pct_revenue"]) - 1)]
        da = revenue * drivers["da_pct_revenue"]
        ebit = gross_profit - sga - rd - da
        tax_rate = drivers["tax_rate"]
        tax = max(ebit, 0) * tax_rate
        net_income = ebit - tax
        capex = revenue * drivers["capex_pct_revenue"]
        nwc_pct = drivers["nwc_pct_revenue"] + i * drivers.get("nwc_pct_revenue_delta_per_year", 0)
        nwc = revenue * nwc_pct
        delta_nwc = nwc - prev_nwc
        fcf = ebit * (1 - tax_rate) + da - capex - delta_nwc

        cash += fcf
        equity += net_income
        # Simplified: no dividends in base — retained earnings flow to equity; debt held flat
        interest = debt * drivers.get("interest_rate", 0.045)
        total_assets = equity + debt + (cash if cash > 0 else 0)

        rows.append(
            {
                "fiscal_year": fy,
                "period": "forecast",
                "revenue": revenue,
                "cogs": cogs,
                "gross_profit": gross_profit,
                "sga": sga,
                "rd": rd,
                "da": da,
                "ebit": ebit,
                "tax": tax,
                "net_income": net_income,
                "capex": capex,
                "delta_nwc": delta_nwc,
                "unlevered_fcf": fcf,
                "cash": cash,
                "total_debt": debt,
                "equity": equity,
                "total_assets": total_assets,
                "gross_margin": gm,
                "ebit_margin": ebit / revenue if revenue else None,
            }
        )
        prev_rev = revenue
        prev_nwc = nwc

    fc = pd.DataFrame(rows)
    actual = hist.copy()
    actual["period"] = "actual"
    for c in ["sga", "rd", "ebit", "tax", "delta_nwc", "unlevered_fcf", "gross_margin", "ebit_margin"]:
        if c not in actual.columns:
            actual[c] = np.nan
    if "ebit" not in actual.columns and "operating_income" in actual.columns:
        actual["ebit"] = actual["operating_income"]
    if "gross_margin" not in actual.columns or actual["gross_margin"].isna().all():
        actual["gross_margin"] = actual["gross_profit"] / actual["revenue"]

    combined = pd.concat([actual, fc], ignore_index=True, sort=False)
    return combined
