"""Presentation dates for point-in-time case studies (memo / PDF / logs)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from src.data_pull import parse_cutoff


def published_timestamp(research: dict[str, Any], knowledge_cutoff: pd.Timestamp | None) -> pd.Timestamp:
    """
    Wall-clock time shown in outputs when replaying a historical memo.
    Defaults to knowledge_cutoff, then memo_date, for point-in-time runs.
    """
    if research.get("published_at"):
        return pd.Timestamp(research["published_at"]).normalize()
    if knowledge_cutoff is not None:
        return knowledge_cutoff.normalize()
    if research.get("memo_date"):
        return pd.Timestamp(research["memo_date"]).normalize()
    return pd.Timestamp.now("UTC").normalize()


def published_label(ts: pd.Timestamp) -> str:
    return ts.strftime("%d %B %Y")


def published_iso(ts: pd.Timestamp) -> str:
    return f"{ts.strftime('%Y-%m-%d')}T16:00:00+00:00"


def to_reportlab_datetime(ts: pd.Timestamp) -> datetime:
    return datetime(ts.year, ts.month, ts.day, 16, 0, 0)


def load_research_dates(cfg: dict[str, Any]) -> tuple[dict[str, Any], pd.Timestamp | None, pd.Timestamp]:
    research = cfg.get("research") or {}
    data_mode = (research.get("data_mode") or "latest").lower()
    cutoff = parse_cutoff(research.get("knowledge_cutoff")) if data_mode == "point_in_time" else None
    if data_mode == "point_in_time":
        published = published_timestamp(research, cutoff)
    else:
        published = pd.Timestamp.now("UTC").normalize()
    return research, cutoff, published
