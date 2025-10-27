"""Fetch transport reliability data for Sydney."""
from __future__ import annotations

import logging
from typing import Callable

import pandas as pd
from pandas import DataFrame

from ..config import DATASET_CONFIGS
from ..utils_io import current_timestamp, sha256sum, update_registry, write_dataframe

logger = logging.getLogger(__name__)
CONFIG = DATASET_CONFIGS["transport"]


def _transform_remote(df: DataFrame) -> DataFrame:
    required = ["pickup", "dropoff", "pickup_zone", "dropoff_zone", "distance", "total", "passengers"]
    if not set(required).issubset(df.columns):
        raise ValueError("Transport dataset missing expected columns")
    trimmed = df.loc[:, required].copy()
    trimmed.rename(
        columns={
            "pickup": "service_start",
            "dropoff": "service_end",
            "pickup_zone": "origin",
            "dropoff_zone": "destination",
            "total": "total_fare",
        },
        inplace=True,
    )
    trimmed["mode"] = "Taxi"
    trimmed["record_id"] = range(1, len(trimmed) + 1)
    return trimmed


def _fallback() -> DataFrame:
    data = [
        {
            "record_id": 1,
            "service_start": "2023-05-01T07:30:00Z",
            "service_end": "2023-05-01T08:05:00Z",
            "origin": "Parramatta",
            "destination": "Sydney CBD",
            "mode": "Train",
            "distance": 22.3,
            "passengers": 320,
            "total_fare": 5.6,
        },
        {
            "record_id": 2,
            "service_start": "2023-05-01T08:10:00Z",
            "service_end": "2023-05-01T08:42:00Z",
            "origin": "Chatswood",
            "destination": "Sydney CBD",
            "mode": "Train",
            "distance": 12.4,
            "passengers": 210,
            "total_fare": 4.1,
        },
        {
            "record_id": 3,
            "service_start": "2023-05-01T09:05:00Z",
            "service_end": "2023-05-01T09:35:00Z",
            "origin": "Surry Hills",
            "destination": "Randwick",
            "mode": "Bus",
            "distance": 6.8,
            "passengers": 55,
            "total_fare": 3.2,
        },
    ]
    return pd.DataFrame(data)


def fetch_transport(transform: Callable[[DataFrame], DataFrame] | None = None) -> str:
    transform = transform or _transform_remote
    try:
        raw = pd.read_csv(CONFIG.source_url)
        dataset = transform(raw).head(1000)
        logger.info("Fetched transport data from %s", CONFIG.source_url)
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("Falling back to synthetic transport sample: %s", exc)
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
    fetch_transport()

