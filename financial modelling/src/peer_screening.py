"""Screen peer universe and export comparability metrics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf

from src.data_pull import fetch_company_snapshot


def screen_peers(
    tickers: list[str],
    subject_ticker: str,
    min_market_cap_usd: float = 1e9,
) -> pd.DataFrame:
    rows = []
    for tk in tickers:
        snap = fetch_company_snapshot(tk)
        t = yf.Ticker(tk)
        info = t.info or {}
        mcap = info.get("marketCap")
        if mcap is not None and mcap < min_market_cap_usd and tk != subject_ticker:
            continue
        rows.append(
            {
                "ticker": tk,
                "name": snap.name,
                "sector": snap.sector,
                "industry": snap.industry,
                "market_cap_usd": mcap,
                "price": snap.price,
                "currency": snap.currency,
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    sub_sector = df.loc[df["ticker"] == subject_ticker, "sector"]
    if not sub_sector.empty and sub_sector.iloc[0]:
        same = df["sector"] == sub_sector.iloc[0]
        df["same_sector_as_subject"] = same
    else:
        df["same_sector_as_subject"] = True
    return df.sort_values("market_cap_usd", ascending=False, na_position="last")


def export_peer_screen(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
