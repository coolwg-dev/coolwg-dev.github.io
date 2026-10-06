"""Chart outputs for the case study."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def _style():
    sns.set_theme(style="whitegrid", context="talk", font_scale=0.85)


def _suptitle(fig, title: str, subtitle: str | None) -> None:
    if subtitle:
        fig.suptitle(title, fontsize=14, y=0.98)
        fig.text(0.5, 0.93, subtitle, ha="center", fontsize=10, color="#555555")
    else:
        fig.suptitle(title, fontsize=14)


def plot_revenue_ebit_forecast(combined: pd.DataFrame, out: Path, subtitle: str | None = None) -> None:
    _style()
    df = combined.dropna(subset=["revenue"]).copy()
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = df["period"].map({"actual": "#1f77b4", "forecast": "#ff7f0e"})
    ax.bar(df["fiscal_year"].astype(str), df["revenue"], color=colors, alpha=0.85, label="Revenue")
    if "ebit" in df.columns:
        ax.plot(df["fiscal_year"].astype(str), df["ebit"], color="#2ca02c", marker="o", linewidth=2, label="EBIT")
    ax.set_ylabel("USD millions")
    ax.legend(["Revenue (actual)", "Revenue (forecast)", "EBIT"], loc="upper left")
    _suptitle(fig, "Revenue and EBIT — Actual vs Forecast (USD m)", subtitle)
    fig.tight_layout(rect=(0, 0, 1, 0.9) if subtitle else None)
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_dcf_sensitivity(pivot: pd.DataFrame, out: Path, subtitle: str | None = None) -> None:
    _style()
    table = pivot.pivot(index="wacc", columns="terminal_growth", values="implied_price")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.heatmap(table, annot=True, fmt=".1f", cmap="RdYlGn", ax=ax)
    ax.set_xlabel("Terminal growth")
    ax.set_ylabel("WACC")
    _suptitle(fig, "DCF sensitivity — implied share price (HKD proxy via USD)", subtitle)
    fig.tight_layout(rect=(0, 0, 1, 0.9) if subtitle else None)
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_scenarios(
    scenarios: pd.DataFrame, spot: float | None, out: Path, subtitle: str | None = None
) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(8, 4))
    x = scenarios["scenario"]
    y = scenarios["implied_price_hkd"] if "implied_price_hkd" in scenarios.columns else scenarios["implied_price"]
    ax.bar(x, y, color=["#4c78a8", "#59a14f", "#e15759"])
    if spot:
        ax.axhline(spot, color="black", linestyle="--", label=f"Spot ~{spot:.1f} HKD")
    ax.set_ylabel("HKD per share")
    ax.legend()
    _suptitle(fig, "Triangulated DCF scenarios — implied price", subtitle)
    fig.tight_layout(rect=(0, 0, 1, 0.9) if subtitle else None)
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_trading_comps(comps: pd.DataFrame, subject: str, out: Path, subtitle: str | None = None) -> None:
    _style()
    df = comps.dropna(subset=["ev_ebitda"]).copy()
    fig, ax = plt.subplots(figsize=(9, 4))
    colors = ["#e15759" if t == subject else "#4c78a8" for t in df["ticker"]]
    ax.barh(df["ticker"], df["ev_ebitda"], color=colors)
    ax.set_xlabel("x")
    _suptitle(fig, "Trading comps — EV / EBITDA", subtitle)
    fig.tight_layout(rect=(0, 0, 1, 0.9) if subtitle else None)
    fig.savefig(out, dpi=150)
    plt.close(fig)
