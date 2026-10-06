"""Run full HK equity case study pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.charts import (
    plot_dcf_sensitivity,
    plot_revenue_ebit_forecast,
    plot_scenarios,
    plot_trading_comps,
)
from src.comps import fetch_hkd_usd, implied_valuation_from_comps, trading_comps_table, transaction_comps_table
from src.data_pull import (
    fetch_company_snapshot,
    fetch_historical_financials,
    filter_financials_to_cutoff,
    historical_to_wide,
    save_data_bundle,
)
from src.dcf import run_dcf, scenario_valuation, sensitivity_margins, sensitivity_wacc_growth
from src.peer_screening import export_peer_screen, screen_peers
from src.presentation import load_research_dates, published_iso, published_label
from src.three_statement import build_forecast, calibrate_drivers


def load_config() -> dict:
    with open(ROOT / "config" / "case_study.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    cfg = load_config()
    ticker = cfg["company"]["ticker"]
    research, knowledge_cutoff, published = load_research_dates(cfg)
    data_mode = (research.get("data_mode") or "latest").lower()
    memo_date = research.get("memo_date")
    chart_caption = f"As of {published_label(published)} (point-in-time)" if knowledge_cutoff else None
    out = ROOT / "outputs"
    data_dir = out / "data"
    fig_dir = out / "figures"
    out.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    save_data_bundle(ticker, data_dir, as_of=knowledge_cutoff)
    snap = fetch_company_snapshot(ticker, as_of=knowledge_cutoff)
    fin = fetch_historical_financials(ticker)
    if knowledge_cutoff is not None:
        fin = filter_financials_to_cutoff(fin, knowledge_cutoff)
    hist = historical_to_wide(fin)
    last_actual_year = int(hist.iloc[-1]["fiscal_year"]) if not hist.empty else None

    peers = screen_peers(cfg["peers"]["trading"], ticker)
    export_peer_screen(peers, out / "peer_screen.csv")

    drivers = calibrate_drivers(hist, cfg["drivers"])
    years = cfg["forecast"]["years"]
    start = cfg["forecast"]["start_calendar_year"]
    combined = build_forecast(hist, drivers, years, start)
    combined.to_csv(out / "three_statement_forecast.csv", index=False)

    last = hist.iloc[-1]
    cash = float(last.get("cash") or 0)
    debt = float(last.get("total_debt") or 0)
    shares = snap.shares_outstanding

    hkd_usd = fetch_hkd_usd(knowledge_cutoff)

    dcf_cfg = cfg["dcf"].copy()
    dcf_cfg["tax_shield"] = cfg["drivers"]["tax_rate"]
    base_dcf = run_dcf(combined, dcf_cfg, cash, debt, shares)
    sens = sensitivity_wacc_growth(combined, dcf_cfg, cash, debt, shares)
    sens.to_csv(out / "dcf_sensitivity_wacc_growth.csv", index=False)
    margin_sens = sensitivity_margins(
        hist, drivers, years, start, dcf_cfg, cash, debt, shares, [-0.02, -0.01, 0, 0.01, 0.02]
    )
    margin_sens.to_csv(out / "dcf_sensitivity_margin.csv", index=False)
    scenarios = scenario_valuation(
        hist, drivers, years, start, dcf_cfg, cfg["scenarios"], cash, debt, shares
    )
    scenarios["implied_price_hkd"] = scenarios["implied_price"] / hkd_usd
    scenarios.to_csv(out / "dcf_scenarios.csv", index=False)

    comps = trading_comps_table(cfg["peers"]["trading"], as_of=knowledge_cutoff)
    comps.to_csv(out / "trading_comps.csv", index=False)
    sub_row = comps[comps["ticker"] == ticker].iloc[0]
    subject_metrics = {
        "ebitda_usd_m": sub_row.get("ebitda_usd_m"),
        "revenue_usd_m": sub_row.get("revenue_usd_m"),
        "net_income_usd_m": sub_row.get("net_income_usd_m"),
        "net_debt_usd_m": debt - cash,
        "shares": shares,
    }
    implied = implied_valuation_from_comps(subject_metrics, comps, ticker, hkd_usd)
    implied.to_csv(out / "comps_implied_valuation.csv", index=False)

    txns = transaction_comps_table(cfg["peers"]["transactions"])
    txns.to_csv(out / "transaction_comps.csv", index=False)

    plot_revenue_ebit_forecast(combined, fig_dir / "revenue_ebit_forecast.png", subtitle=chart_caption)
    plot_dcf_sensitivity(sens, fig_dir / "dcf_sensitivity.png", subtitle=chart_caption)
    plot_scenarios(scenarios, snap.price, fig_dir / "dcf_scenarios.png", subtitle=chart_caption)
    plot_trading_comps(comps, ticker, fig_dir / "trading_comps_ev_ebitda.png", subtitle=chart_caption)

    dcf_hkd = base_dcf.value_per_share / hkd_usd if base_dcf.value_per_share else None
    upside = None
    if dcf_hkd and snap.price:
        upside = dcf_hkd / snap.price - 1

    summary = {
        "company": cfg["company"],
        "research": {
            "memo_date": memo_date,
            "published_at": str(published.date()),
            "data_mode": data_mode,
            "knowledge_cutoff": str(knowledge_cutoff.date()) if knowledge_cutoff is not None else None,
            "last_actual_fiscal_year": last_actual_year,
        },
        "published_at": published_iso(published),
        "pipeline_run_at": published_iso(published),
        "spot_price_hkd": snap.price,
        "spot_price_as_of": "knowledge_cutoff" if knowledge_cutoff is not None else "latest_market",
        "fx_hkd_usd": hkd_usd,
        "base_dcf": {**base_dcf.__dict__, "value_per_share_hkd": dcf_hkd},
        "dcf_upside_vs_spot": upside,
        "recommendation": cfg["recommendation"]["base_case_rating"],
        "outputs": {
            "forecast": str(out / "three_statement_forecast.csv"),
            "memo": str(ROOT / "docs" / "INVESTMENT_MEMO.md"),
        },
    }
    with open(out / "valuation_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"Case study complete: {ticker}")
    print(f"  Published (presentation): {published_label(published)}")
    if data_mode == "point_in_time" and knowledge_cutoff is not None:
        print(f"  Data mode: point_in_time (cutoff {knowledge_cutoff.date()})")
    else:
        print(f"  Data mode: latest (last actual FY {last_actual_year}, spot = current market)")
    print(f"  Spot: {snap.price} HKD")
    print(
        f"  Base DCF implied: {base_dcf.value_per_share:.2f} USD / {dcf_hkd:.1f} HKD "
        f"(WACC {base_dcf.wacc:.1%}, g {base_dcf.terminal_growth:.1%})"
    )
    if upside is not None:
        print(f"  DCF upside vs spot: {upside:.1%}")
    print(f"  Rating (base case): {cfg['recommendation']['base_case_rating']}")
    print(f"  Outputs: {out}")


if __name__ == "__main__":
    main()
