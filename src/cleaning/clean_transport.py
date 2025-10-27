"""Clean transport reliability data."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
from pandas import DataFrame
from zoneinfo import ZoneInfo

from ..config import DATASET_CONFIGS
from ..utils_io import write_dataframe
from .utils import canonicalize_area_name, ensure_columns, reorder_columns

logger = logging.getLogger(__name__)
CONFIG = DATASET_CONFIGS["transport"]
RAW_COLUMNS = [
    "record_id",
    "service_start",
    "service_end",
    "origin",
    "destination",
    "mode",
    "distance",
    "passengers",
    "total_fare",
]
CLEAN_COLUMNS = [
    "service_id",
    "service_timestamp",
    "origin_suburb",
    "origin_sa2",
    "destination_suburb",
    "destination_sa2",
    "mode",
    "duration_minutes",
    "delay_minutes",
    "load_factor",
    "fare_total",
    "status",
]

SA2_LOOKUP: Dict[str, str] = {
    "Sydney Cbd": "117011321",
    "Sydney CBD": "117011321",
    "Parramatta": "125021656",
    "Chatswood": "121041392",
    "Surry Hills": "117011322",
    "Randwick": "118011342",
    "Sydney Olympic Park": "125021657",
}


def enforce_schema(df: DataFrame) -> DataFrame:
    ensure_columns(df, CLEAN_COLUMNS)
    ordered = reorder_columns(df, CLEAN_COLUMNS)
    ordered["service_timestamp"] = pd.to_datetime(ordered["service_timestamp"], errors="coerce")
    if ordered["service_timestamp"].isna().any():
        raise ValueError("service_timestamp contains nulls after cleaning")
    return ordered


def clean_transport(raw_path: str | None = None, output_path: str | None = None) -> DataFrame:
    raw_path = raw_path or str(CONFIG.raw_path)
    output_path = output_path or str(CONFIG.interim_path)
    df = pd.read_csv(raw_path)
    ensure_columns(df, RAW_COLUMNS)
    tz = ZoneInfo("Australia/Sydney")
    start = pd.to_datetime(df["service_start"], utc=True, errors="coerce")
    end = pd.to_datetime(df["service_end"], utc=True, errors="coerce")
    start = start.dt.tz_convert(tz)
    end = end.dt.tz_convert(tz)

    duration = (end - start).dt.total_seconds() / 60.0
    distance_km = pd.to_numeric(df["distance"], errors="coerce").fillna(0) * 1.60934
    expected_duration = (distance_km / 30.0) * 60.0
    delay = (duration - expected_duration).clip(lower=0)

    origins = df["origin"].map(canonicalize_area_name)
    destinations = df["destination"].map(canonicalize_area_name)

    mode = df["mode"].fillna("Unknown").str.title()
    capacities = mode.map({"Train": 1200, "Metro": 1100, "Bus": 80, "Ferry": 400, "Taxi": 4}).fillna(100)
    passengers = pd.to_numeric(df["passengers"], errors="coerce").fillna(0)
    load_factor = (passengers / capacities).clip(lower=0, upper=1)

    cleaned = pd.DataFrame(
        {
            "service_id": df.get("record_id", pd.RangeIndex(start=1, stop=len(df) + 1)),
            "service_timestamp": start,
            "origin_suburb": origins,
            "origin_sa2": origins.map(SA2_LOOKUP).fillna("UNKNOWN"),
            "destination_suburb": destinations,
            "destination_sa2": destinations.map(SA2_LOOKUP).fillna("UNKNOWN"),
            "mode": mode,
            "duration_minutes": duration.round(2),
            "delay_minutes": delay.round(2),
            "load_factor": load_factor.round(3),
            "fare_total": pd.to_numeric(df["total_fare"], errors="coerce").fillna(0).round(2),
            "status": np.where(delay > 5, "delayed", "ontime"),
        }
    )

    cleaned = cleaned.dropna(subset=["service_timestamp", "origin_suburb", "destination_suburb"])
    cleaned = enforce_schema(cleaned)
    write_dataframe(cleaned, Path(output_path))
    logger.info("Wrote cleaned transport data to %s", output_path)
    return cleaned


if __name__ == "__main__":
    clean_transport()

