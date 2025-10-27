"""Fetch daily weather observations."""
from __future__ import annotations

import logging
from typing import Callable

import pandas as pd
from pandas import DataFrame

from ..config import DATASET_CONFIGS
from ..utils_io import current_timestamp, sha256sum, update_registry, write_dataframe

logger = logging.getLogger(__name__)
CONFIG = DATASET_CONFIGS["weather"]


def _transform_remote(df: DataFrame) -> DataFrame:
    required = ["date", "precipitation", "temp_max", "temp_min", "weather"]
    if not set(required).issubset(df.columns):
        raise ValueError("Weather dataset missing expected columns")
    trimmed = df.loc[:, required].copy()
    dt = pd.to_datetime(trimmed.pop("date"), errors="coerce")
    trimmed["observation_time"] = (dt + pd.to_timedelta(12, unit="h")).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    trimmed.rename(
        columns={
            "precipitation": "rain_mm",
            "temp_max": "temp_max_c",
            "temp_min": "temp_min_c",
            "weather": "observation_type",
        },
        inplace=True,
    )
    trimmed["station_name"] = "Sydney Observatory Hill"
    trimmed["suburb"] = "Sydney CBD"
    return trimmed


def _fallback() -> DataFrame:
    data = [
        {
            "observation_time": "2023-05-01T12:00:00Z",
            "rain_mm": 2.0,
            "temp_max_c": 22.5,
            "temp_min_c": 14.2,
            "observation_type": "rain",
            "station_name": "Sydney Observatory Hill",
            "suburb": "Sydney CBD",
        },
        {
            "observation_time": "2023-05-02T12:00:00Z",
            "rain_mm": 0.0,
            "temp_max_c": 24.0,
            "temp_min_c": 13.9,
            "observation_type": "sun",
            "station_name": "Sydney Observatory Hill",
            "suburb": "Sydney CBD",
        },
        {
            "observation_time": "2023-05-03T12:00:00Z",
            "rain_mm": 5.2,
            "temp_max_c": 19.0,
            "temp_min_c": 11.0,
            "observation_type": "rain",
            "station_name": "Sydney Observatory Hill",
            "suburb": "Sydney CBD",
        },
    ]
    return pd.DataFrame(data)


def fetch_weather(transform: Callable[[DataFrame], DataFrame] | None = None) -> str:
    transform = transform or _transform_remote
    try:
        raw = pd.read_csv(CONFIG.source_url)
        dataset = transform(raw).head(1000)
        logger.info("Fetched weather data from %s", CONFIG.source_url)
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("Falling back to synthetic weather sample: %s", exc)
        dataset = _fallback()
    write_dataframe(dataset, CONFIG.raw_path)
    metadata = {
        "dataset": CONFIG.name,
        "description": CONFIG.description,
        "source_url": CONFIG.source_url,
        "path": str(CONFIG.raw_path),
        "fetched_at": current_timestamp(),
        "rows": int(dataset.shape[0]),
        "columns": list(dataset.columns),
        "checksum": sha256sum(CONFIG.raw_path),
    }
    update_registry(CONFIG.name, metadata)
    return str(CONFIG.raw_path)


if __name__ == "__main__":
    fetch_weather()

