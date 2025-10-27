"""Shared utilities for cleaning modules."""
from __future__ import annotations

import re
from typing import Sequence

import pandas as pd
from pandas import Timestamp
from zoneinfo import ZoneInfo

ALIASES = {
    "sydney cbd": "Sydney CBD",
    "cbd": "Sydney CBD",
    "central business district": "Sydney CBD",
    "newtown": "Newtown",
    "parramatta": "Parramatta",
    "chatswood": "Chatswood",
    "bondi beach": "Bondi Beach",
    "surry hills": "Surry Hills",
    "redfern": "Redfern",
    "randwick": "Randwick",
    "olympic park": "Sydney Olympic Park",
    "sydney olympic park": "Sydney Olympic Park",
}


def canonicalize_area_name(name: object) -> str | None:
    """Return a canonical Sydney area name."""
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return None
    text = str(name).strip()
    if not text:
        return None
    text = re.sub(r"\s+", " ", text)
    key = text.lower()
    return ALIASES.get(key, text.title())


def localize_timestamp(value: object, tz: str = "Australia/Sydney") -> Timestamp | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    tzinfo = ZoneInfo(tz)
    ts = pd.to_datetime(value, utc=True, errors='coerce')
    if pd.isna(ts):
        ts = pd.to_datetime(value, errors='coerce')
        if pd.isna(ts):
            return None
        if isinstance(ts, pd.Series):
            ts = ts.dt.tz_localize(tzinfo)
            return ts
        return ts.tz_localize(tzinfo)
    if isinstance(ts, pd.Series):
        return ts.dt.tz_convert(tzinfo)
    return ts.tz_convert(tzinfo)


def ensure_columns(df: pd.DataFrame, required: Sequence[str]) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def reorder_columns(df: pd.DataFrame, order: Sequence[str]) -> pd.DataFrame:
    return df.loc[:, list(order)]


__all__ = ["canonicalize_area_name", "localize_timestamp", "ensure_columns", "reorder_columns"]

