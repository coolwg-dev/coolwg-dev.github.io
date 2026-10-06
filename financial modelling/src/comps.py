"""Trading and transaction comparable multiples."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

from src.data_pull import (
    _on_or_before,
    _row_value,
    fetch_historical_financials,
    fetch_price_as_of,
    filter_financials_to_cutoff,
)


def _to_millions(value: float | None) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if abs(value) >= 1e9:
        return float(value) / 1e6
    if abs(value) >= 1e6:
        return float(value) / 1e6
    return float(value)


def fetch_hkd_usd(as_of: pd.Timestamp | None = None) -> float:
    if as_of is not None:
        start = as_of - pd.Timedelta(days=14)
        end = as_of + pd.Timedelta(days=1)
        fx = yf.Ticker("HKDUSD=X").history(start=start.date(), end=end.date())
        if not fx.empty:
            fx = fx[_on_or_before(fx.index, as_of)]
            if not fx.empty:
                return float(fx["Close"].iloc[-1])
    fx = yf.Ticker("HKDUSD=X").history(period="5d")
    if fx.empty:
        return 0.128
    return float(fx["Close"].iloc[-1])


def _ttm_metrics(ticker: str, hkd_usd: float, as_of: pd.Timestamp | None = None) -> dict[str, float | None]:
    t = yf.Ticker(ticker)
    info = t.info or {}
    fin = fetch_historical_financials(ticker)
    if as_of is not None:
        fin = filter_financials_to_cutoff(fin, as_of)
    inc = fin["income"]
    bal = fin["balance"]
    col = inc.columns[0] if inc is not None and not inc.empty else None

    revenue = _row_value(inc, ["Total Revenue", "Operating Revenue"], col) if col else None
    ebitda = info.get("ebitda") if as_of is None else None
    if ebitda is None and col is not None:
        op = _row_value(inc, ["Operating Income", "EBIT"], col)
        da = _row_value(t.cashflow, ["Depreciation And Amortization"], col)
        if op is not None and da is not None:
            ebitda = op + da
    net_income = _row_value(inc, ["Net Income"], col) if col else None

    listing_ccy = info.get("currency") or "USD"
    fin_ccy = info.get("financialCurrency") or "USD"
    if as_of is not None:
        spot = fetch_price_as_of(ticker, as_of)
        shares = info.get("sharesOutstanding")
        mcap_raw = spot * shares if spot and shares else info.get("marketCap")
    else:
        mcap_raw = info.get("marketCap")
    debt = _row_value(bal, ["Total Debt"], col) if col else info.get("totalDebt")
    cash = _row_value(bal, ["Cash And Cash Equivalents"], col) if col else info.get("totalCash")
    ev_raw = None
    if mcap_raw is not None:
        ev_raw = mcap_raw + (debt or 0) - (cash or 0)

    def to_usd_raw(amount: float | None) -> float | None:
        if amount is None:
            return None
        if listing_ccy == "HKD" and fin_ccy == "USD":
            return amount * hkd_usd
        return amount

    ev_usd = to_usd_raw(ev_raw)
    mcap_usd = to_usd_raw(mcap_raw)
    revenue_m = _to_millions(revenue)
    ebitda_m = _to_millions(ebitda)
    ni_m = _to_millions(net_income)

    pe = info.get("trailingPE") if as_of is None else None
    if pe is None and mcap_usd and ni_m and ni_m > 0:
        pe = (mcap_usd / 1e6) / ni_m

    ev_ebitda = None
    if ev_usd and ebitda_m and ebitda_m > 0:
        ev_ebitda = (ev_usd / 1e6) / ebitda_m
    ev_rev = None
    if ev_usd and revenue_m and revenue_m > 0:
        ev_rev = (ev_usd / 1e6) / revenue_m

    return {
        "ticker": ticker,
        "market_cap_usd_m": _to_millions(mcap_usd),
        "enterprise_value_usd_m": _to_millions(ev_usd),
        "revenue_usd_m": revenue_m,
        "ebitda_usd_m": ebitda_m,
        "net_income_usd_m": ni_m,
        "pe": pe,
        "ev_ebitda": ev_ebitda,
        "ev_revenue": ev_rev,
    }


def trading_comps_table(tickers: list[str], as_of: pd.Timestamp | None = None) -> pd.DataFrame:
    hkd_usd = fetch_hkd_usd(as_of)
    rows = [_ttm_metrics(tk, hkd_usd, as_of=as_of) for tk in tickers]
    return pd.DataFrame(rows)


def implied_valuation_from_comps(
    subject_metrics: dict[str, float],
    comps: pd.DataFrame,
    subject_ticker: str,
    hkd_usd: float,
) -> pd.DataFrame:
    peer = comps[comps["ticker"] != subject_ticker]
    medians = {
        "ev_ebitda": peer["ev_ebitda"].median(),
        "ev_revenue": peer["ev_revenue"].median(),
        "pe": peer["pe"].median(),
    }
    ebitda = subject_metrics.get("ebitda_usd_m")
    revenue = subject_metrics.get("revenue_usd_m")
    ni = subject_metrics.get("net_income_usd_m")
    net_debt_m = subject_metrics.get("net_debt_usd_m", 0)
    shares = subject_metrics.get("shares")

    rows = []
    if ebitda and medians["ev_ebitda"]:
        ev = medians["ev_ebitda"] * ebitda
        eq = ev - net_debt_m
        rows.append({"method": "EV/EBITDA (peer median)", "enterprise_value_usd_m": ev, "equity_value_usd_m": eq})
    if revenue and medians["ev_revenue"]:
        ev = medians["ev_revenue"] * revenue
        eq = ev - net_debt_m
        rows.append({"method": "EV/Revenue (peer median)", "enterprise_value_usd_m": ev, "equity_value_usd_m": eq})
    if ni and medians["pe"]:
        eq = medians["pe"] * ni
        rows.append({"method": "P/E (peer median)", "enterprise_value_usd_m": np.nan, "equity_value_usd_m": eq})

    out = pd.DataFrame(rows)
    if shares and shares > 0 and not out.empty:
        out["implied_price_usd"] = out["equity_value_usd_m"] * 1e6 / shares
        out["implied_price_hkd"] = out["implied_price_usd"] / hkd_usd
    return out


def transaction_comps_table(txns: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(txns)
