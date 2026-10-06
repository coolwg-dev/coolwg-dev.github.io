"""Discounted cash flow and scenario valuation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class DCFResult:
    wacc: float
    terminal_growth: float
    pv_explicit: float
    pv_terminal: float
    enterprise_value: float
    equity_value: float
    value_per_share: float | None
    net_debt: float


def compute_wacc(dcf_cfg: dict[str, Any]) -> float:
    rf = dcf_cfg["risk_free_rate"]
    erp = dcf_cfg["equity_risk_premium"]
    beta = dcf_cfg["beta"]
    ke = rf + beta * erp
    kd = dcf_cfg["cost_of_debt_pretax"] * (1 - dcf_cfg.get("tax_shield", 0.175))
    wd = dcf_cfg["target_debt_to_capital"]
    we = 1 - wd
    return we * ke + wd * kd


def run_dcf(
    forecast: pd.DataFrame,
    dcf_cfg: dict[str, Any],
    cash: float,
    debt: float,
    shares: float | None,
    terminal_growth: float | None = None,
    wacc_override: float | None = None,
) -> DCFResult:
    wacc = wacc_override if wacc_override is not None else compute_wacc(dcf_cfg)
    tg = terminal_growth if terminal_growth is not None else dcf_cfg["terminal_growth"]

    fc = forecast[forecast["period"] == "forecast"].copy()
    if fc.empty:
        raise ValueError("Forecast rows required for DCF.")
    fcf = fc["unlevered_fcf"].astype(float).values
    years = np.arange(1, len(fcf) + 1)
    pv_explicit = float(np.sum(fcf / (1 + wacc) ** years))
    terminal_fcf = fcf[-1] * (1 + tg)
    tv = terminal_fcf / (wacc - tg)
    pv_terminal = float(tv / (1 + wacc) ** len(fcf))
    ev = pv_explicit + pv_terminal
    net_debt = debt - cash
    equity = ev - net_debt
    vps = equity / shares if shares and shares > 0 else None
    # shares from yfinance are raw count; equity in USD millions
    if vps is not None and equity < 1e5:
        vps = equity * 1e6 / shares

    return DCFResult(
        wacc=wacc,
        terminal_growth=tg,
        pv_explicit=pv_explicit,
        pv_terminal=pv_terminal,
        enterprise_value=ev,
        equity_value=equity,
        value_per_share=vps,
        net_debt=net_debt,
    )


def sensitivity_wacc_growth(
    forecast: pd.DataFrame,
    dcf_cfg: dict[str, Any],
    cash: float,
    debt: float,
    shares: float | None,
) -> pd.DataFrame:
    base_wacc = compute_wacc(dcf_cfg)
    bps = dcf_cfg.get("wacc_sensitivity_bps", [-150, -75, 0, 75, 150])
    growths = dcf_cfg.get("terminal_growth_sensitivity", [0.015, 0.02, 0.025, 0.03, 0.035])
    rows = []
    for bp in bps:
        w = base_wacc + bp / 10000
        for g in growths:
            if w <= g:
                val = np.nan
            else:
                res = run_dcf(forecast, dcf_cfg, cash, debt, shares, terminal_growth=g, wacc_override=w)
                val = res.value_per_share
            rows.append({"wacc": w, "terminal_growth": g, "implied_price": val})
    return pd.DataFrame(rows)


def sensitivity_margins(
    hist: pd.DataFrame,
    drivers: dict[str, Any],
    years: int,
    start_year: int,
    dcf_cfg: dict[str, Any],
    cash: float,
    debt: float,
    shares: float | None,
    margin_shifts: list[float],
) -> pd.DataFrame:
    from src.three_statement import build_forecast

    rows = []
    for shift in margin_shifts:
        d = drivers.copy()
        d["gross_margin"] = [m + shift for m in drivers["gross_margin"]]
        fc = build_forecast(hist, d, years, start_year)
        res = run_dcf(fc, dcf_cfg, cash, debt, shares)
        rows.append({"gross_margin_shift": shift, "implied_price": res.value_per_share})
    return pd.DataFrame(rows)


def scenario_valuation(
    hist: pd.DataFrame,
    base_drivers: dict[str, Any],
    years: int,
    start_year: int,
    dcf_cfg: dict[str, Any],
    scenarios: dict[str, Any],
    cash: float,
    debt: float,
    shares: float | None,
) -> pd.DataFrame:
    from src.three_statement import build_forecast

    results = []
    for name, adj in [("base", {}), ("bull", scenarios["bull"]), ("bear", scenarios["bear"])]:
        d = base_drivers.copy()
        if name != "base":
            d["revenue_growth"] = [g + adj.get("revenue_growth_bump", 0) for g in d["revenue_growth"]]
            d["gross_margin"] = [m + adj.get("gross_margin_bump", 0) for m in d["gross_margin"]]
        fc = build_forecast(hist, d, years, start_year)
        tg = dcf_cfg["terminal_growth"] if name == "base" else adj.get("terminal_growth", dcf_cfg["terminal_growth"])
        wacc = compute_wacc(dcf_cfg) + (adj.get("wacc_bump", 0) if name != "base" else 0)
        res = run_dcf(fc, dcf_cfg, cash, debt, shares, terminal_growth=tg, wacc_override=wacc)
        results.append(
            {
                "scenario": name,
                "wacc": res.wacc,
                "terminal_growth": res.terminal_growth,
                "enterprise_value_usd_m": res.enterprise_value,
                "equity_value_usd_m": res.equity_value,
                "implied_price": res.value_per_share,
            }
        )
    return pd.DataFrame(results)
