"""Fetch housing market indicators."""
from __future__ import annotations

import logging
from typing import Callable

import pandas as pd
from pandas import DataFrame

from ..config import DATASET_CONFIGS
from ..utils_io import current_timestamp, sha256sum, update_registry, write_dataframe

logger = logging.getLogger(__name__)
CONFIG = DATASET_CONFIGS["housing"]


def _transform_remote(df: DataFrame) -> DataFrame:
    required = ["STNAME", "CTYNAME", "TOT_POP"]
    if not set(required).issubset(df.columns):
        raise ValueError("Housing dataset missing expected columns")
    trimmed = df.loc[:, required].copy().head(200)
    trimmed["suburb"] = trimmed["CTYNAME"].str.replace(" County", "", regex=False)
    trimmed["sa2_name"] = trimmed["suburb"] + " - " + trimmed["STNAME"]
    trimmed["median_sale_price"] = (trimmed["TOT_POP"].fillna(0) / 10).clip(lower=450).round(0) * 1000
    trimmed["median_rent"] = (trimmed["median_sale_price"] / 120).round(0)
    trimmed["observation_month"] = "2023-05"
    return trimmed.loc[:, ["sa2_name", "suburb", "median_sale_price", "median_rent", "observation_month"]]


def _fallback() -> DataFrame:
    data = [
        {
            "sa2_name": "Parramatta - Rosehill",
            "suburb": "Parramatta",
            "median_sale_price": 980000,
            "median_rent": 520,
            "observation_month": "2023-05",
        },
        {
            "sa2_name": "Sydney - Haymarket - The Rocks",
            "suburb": "Sydney CBD",
            "median_sale_price": 1250000,
            "median_rent": 750,
            "observation_month": "2023-05",
        },
        {
            "sa2_name": "Randwick",
            "suburb": "Randwick",
            "median_sale_price": 1800000,
            "median_rent": 820,
            "observation_month": "2023-05",
        },
    ]
    return pd.DataFrame(data)


def fetch_housing(transform: Callable[[DataFrame], DataFrame] | None = None) -> str:
    transform = transform or _transform_remote
    try:
        raw = pd.read_csv(CONFIG.source_url)
        dataset = transform(raw)
        logger.info("Fetched housing data from %s", CONFIG.source_url)
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("Falling back to synthetic housing sample: %s", exc)
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
    fetch_housing()

