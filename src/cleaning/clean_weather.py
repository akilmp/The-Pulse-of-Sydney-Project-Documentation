"""Clean weather observations."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from pandas import DataFrame
from zoneinfo import ZoneInfo

from ..config import DATASET_CONFIGS
from ..utils_io import write_dataframe
from .utils import canonicalize_area_name, ensure_columns, reorder_columns

logger = logging.getLogger(__name__)
CONFIG = DATASET_CONFIGS["weather"]
RAW_COLUMNS = [
    "observation_time",
    "rain_mm",
    "temp_max_c",
    "temp_min_c",
    "observation_type",
    "station_name",
    "suburb",
]
CLEAN_COLUMNS = [
    "observation_time",
    "suburb",
    "station_name",
    "rain_mm",
    "temp_max_c",
    "temp_min_c",
    "temp_mean_c",
    "weather_condition",
]


def enforce_schema(df: DataFrame) -> DataFrame:
    ensure_columns(df, CLEAN_COLUMNS)
    df = reorder_columns(df, CLEAN_COLUMNS)
    df["observation_time"] = pd.to_datetime(df["observation_time"], errors="coerce")
    if df["observation_time"].isna().any():
        raise ValueError("observation_time contains nulls")
    numeric_cols = ["rain_mm", "temp_max_c", "temp_min_c", "temp_mean_c"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    return df


def clean_weather(raw_path: str | None = None, output_path: str | None = None) -> DataFrame:
    raw_path = raw_path or str(CONFIG.raw_path)
    output_path = output_path or str(CONFIG.interim_path)
    df = pd.read_csv(raw_path)
    ensure_columns(df, RAW_COLUMNS)

    timestamp = pd.to_datetime(df["observation_time"], utc=True, errors="coerce")
    timestamp = timestamp.dt.tz_convert(ZoneInfo("Australia/Sydney"))

    rain = pd.to_numeric(df["rain_mm"], errors="coerce").clip(lower=0)
    temp_max = pd.to_numeric(df["temp_max_c"], errors="coerce")
    temp_min = pd.to_numeric(df["temp_min_c"], errors="coerce")
    temp_mean = ((temp_max + temp_min) / 2).round(1)

    condition_map = {
        "rain": "rain",
        "sun": "clear",
        "drizzle": "rain",
        "snow": "snow",
        "fog": "fog",
    }
    condition = df["observation_type"].str.lower().map(condition_map).fillna("unknown")

    cleaned = pd.DataFrame(
        {
            "observation_time": timestamp,
            "suburb": df["suburb"].map(canonicalize_area_name),
            "station_name": df["station_name"],
            "rain_mm": rain.round(1),
            "temp_max_c": temp_max.round(1),
            "temp_min_c": temp_min.round(1),
            "temp_mean_c": temp_mean,
            "weather_condition": condition,
        }
    )

    cleaned = cleaned.dropna(subset=["observation_time"]).drop_duplicates(["observation_time", "station_name"])
    cleaned = enforce_schema(cleaned)
    write_dataframe(cleaned, Path(output_path))
    logger.info("Wrote cleaned weather data to %s", output_path)
    return cleaned


if __name__ == "__main__":
    clean_weather()

