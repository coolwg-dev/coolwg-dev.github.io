"""Pull market and financial statement data via yfinance."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf


def parse_cutoff(value: str | date | None) -> pd.Timestamp | None:
    if value is None:
        return None
    return pd.Timestamp(value).normalize()


def _on_or_before(series_index: pd.DatetimeIndex, as_of: pd.Timestamp) -> pd.DatetimeIndex:
    """Boolean mask: index dates on or before as_of (tz-safe)."""
    left = series_index.normalize()
    if series_index.tz is not None:
        right = as_of.tz_localize(series_index.tz) if as_of.tz is None else as_of.tz_convert(series_index.tz)
    else:
        right = as_of.tz_localize(None) if as_of.tz is not None else as_of
    return left <= right.normalize()


@dataclass
class CompanySnapshot:
    ticker: str
    name: str
    price: float | None
    market_cap: float | None
    shares_outstanding: float | None
    currency: str | None
    sector: str | None
    industry: str | None


def _latest_column(df: pd.DataFrame) -> Any:
    if df is None or df.empty:
        return None
    return df.columns[0]


def _row_value(df: pd.DataFrame, labels: list[str], col: Any) -> float | None:
    if df is None or df.empty or col is None:
        return None
    index = {str(i).lower(): i for i in df.index}
    for label in labels:
        key = label.lower()
        if key in index:
            val = df.loc[index[key], col]
            if pd.notna(val):
                return float(val)
    return None


def fetch_price_as_of(ticker: str, as_of: pd.Timestamp) -> float | None:
    """Last adjusted close on or before the knowledge-cutoff date."""
    start = as_of - pd.Timedelta(days=14)
    end = as_of + pd.Timedelta(days=1)
    hist = yf.Ticker(ticker).history(start=start.date(), end=end.date(), auto_adjust=True)
    if hist.empty:
        return None
    hist = hist[_on_or_before(hist.index, as_of)]
    if hist.empty:
        return None
    return float(hist["Close"].iloc[-1])


def filter_financials_to_cutoff(fin: dict[str, pd.DataFrame], as_of: pd.Timestamp) -> dict[str, pd.DataFrame]:
    """Drop statement columns for fiscal periods that had not ended by the cutoff."""
    out: dict[str, pd.DataFrame] = {}
    for key, df in fin.items():
        if df is None or df.empty:
            out[key] = df
            continue
        keep = [c for c in df.columns if pd.Timestamp(c).normalize() <= as_of.normalize()]
        out[key] = df[keep] if keep else df.iloc[:, 0:0]
    return out


def fetch_company_snapshot(ticker: str, as_of: pd.Timestamp | None = None) -> CompanySnapshot:
    t = yf.Ticker(ticker)
    info = t.info or {}
    if as_of is not None:
        price = fetch_price_as_of(ticker, as_of)
    else:
        price = info.get("currentPrice") or info.get("regularMarketPrice")
    return CompanySnapshot(
        ticker=ticker,
        name=info.get("longName") or info.get("shortName") or ticker,
        price=float(price) if price is not None else None,
        market_cap=info.get("marketCap"),
        shares_outstanding=info.get("sharesOutstanding"),
        currency=info.get("currency"),
        sector=info.get("sector"),
        industry=info.get("industry"),
    )


def fetch_historical_financials(ticker: str) -> dict[str, pd.DataFrame]:
    t = yf.Ticker(ticker)
    return {
        "income": t.financials,
        "balance": t.balance_sheet,
        "cashflow": t.cashflow,
    }


def historical_to_wide(fin: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """One row per fiscal period with key line items (USD millions)."""
    inc, bal, cf = fin["income"], fin["balance"], fin["cashflow"]
    if inc is None or inc.empty:
        return pd.DataFrame()

    periods = sorted(inc.columns, reverse=True)
    rows = []
    for col in periods:
        year = pd.Timestamp(col).year
        revenue = _row_value(inc, ["Total Revenue", "Operating Revenue"], col)
        cogs = _row_value(inc, ["Cost Of Revenue", "Reconciled Cost Of Revenue"], col)
        op_income = _row_value(inc, ["Operating Income", "EBIT"], col)
        net_income = _row_value(inc, ["Net Income", "Net Income Common Stockholders"], col)
        interest = _row_value(inc, ["Interest Expense"], col)
        tax = _row_value(inc, ["Tax Provision"], col)
        da = _row_value(cf, ["Depreciation And Amortization", "Depreciation"], col)
        if da is None:
            da = _row_value(inc, ["Reconciled Depreciation"], col)
        capex = _row_value(cf, ["Capital Expenditure"], col)
        total_debt = _row_value(
            bal,
            ["Total Debt", "Long Term Debt And Capital Lease Obligation"],
            col,
        )
        cash = _row_value(bal, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"], col)
        equity = _row_value(bal, ["Stockholders Equity", "Total Equity Gross Minority Interest"], col)
        total_assets = _row_value(bal, ["Total Assets"], col)
        current_assets = _row_value(bal, ["Current Assets", "Total Current Assets"], col)
        current_liab = _row_value(bal, ["Current Liabilities", "Total Current Liabilities"], col)

        gross_profit = revenue - cogs if revenue and cogs else _row_value(inc, ["Gross Profit"], col)
        rows.append(
            {
                "fiscal_year": year,
                "revenue": revenue,
                "cogs": cogs,
                "gross_profit": gross_profit,
                "operating_income": op_income,
                "net_income": net_income,
                "interest_expense": interest,
                "tax_provision": tax,
                "da": da,
                "capex": capex,
                "total_debt": total_debt,
                "cash": cash,
                "equity": equity,
                "total_assets": total_assets,
                "current_assets": current_assets,
                "current_liabilities": current_liab,
            }
        )
    df = pd.DataFrame(rows).sort_values("fiscal_year")
    df = df.dropna(subset=["revenue"])
    # yfinance reports in raw units; scale to millions for readability
    money_cols = [
        c
        for c in df.columns
        if c
        not in ("fiscal_year",)
    ]
    for c in money_cols:
        if df[c].abs().median() > 1e6:
            df[c] = df[c] / 1e6
    return df


def save_data_bundle(
    ticker: str,
    out_dir: Path,
    as_of: pd.Timestamp | None = None,
) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    fin = fetch_historical_financials(ticker)
    if as_of is not None:
        fin = filter_financials_to_cutoff(fin, as_of)
    hist = historical_to_wide(fin)
    snap = fetch_company_snapshot(ticker, as_of=as_of)

    paths = {}
    hist_path = out_dir / f"{ticker.replace('.', '_')}_historical.csv"
    hist.to_csv(hist_path, index=False)
    paths["historical"] = hist_path

    snap_path = out_dir / f"{ticker.replace('.', '_')}_snapshot.csv"
    pd.DataFrame([snap.__dict__]).to_csv(snap_path, index=False)
    paths["snapshot"] = snap_path
    return paths
