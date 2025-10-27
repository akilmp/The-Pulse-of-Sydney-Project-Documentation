"""Fetch demographic indicators resembling ABS releases."""
from __future__ import annotations

import logging
from typing import Callable

import pandas as pd
from pandas import DataFrame

from ..config import DATASET_CONFIGS
from ..utils_io import current_timestamp, sha256sum, update_registry, write_dataframe

logger = logging.getLogger(__name__)
CONFIG = DATASET_CONFIGS["abs"]


def _transform_remote(df: DataFrame) -> DataFrame:
    required = ["STATE", "COUNTY", "AGEGRP", "TOT_POP"]
    if not set(required).issubset(df.columns):
        raise ValueError("ABS dataset missing expected columns")
    # aggregate by county to simulate SA2 profiles
    subset = df[df["AGEGRP"] == 0].copy()
    subset["sa2_code"] = subset["STATE"].astype(str).str.zfill(2) + subset["COUNTY"].astype(str).str.zfill(3)
    subset["sa2_name"] = "SA2 " + subset["sa2_code"]
    subset.rename(columns={"TOT_POP": "population"}, inplace=True)
    subset["median_age"] = 35 + (subset["population"] % 15)
    subset["seifa_score"] = 900 + (subset["population"] % 300)
    return subset.loc[:, ["sa2_code", "sa2_name", "population", "median_age", "seifa_score"]].head(200)


def _fallback() -> DataFrame:
    data = [
        {
            "sa2_code": "117011321",
            "sa2_name": "Sydney - Haymarket - The Rocks",
            "population": 32000,
            "median_age": 33,
            "seifa_score": 1080,
        },
        {
            "sa2_code": "125021656",
            "sa2_name": "Parramatta - Rosehill",
            "population": 54000,
            "median_age": 35,
            "seifa_score": 1012,
        },
        {
            "sa2_code": "118011342",
            "sa2_name": "Randwick",
            "population": 45000,
            "median_age": 36,
            "seifa_score": 1045,
        },
    ]
    return pd.DataFrame(data)


def fetch_abs(transform: Callable[[DataFrame], DataFrame] | None = None) -> str:
    transform = transform or _transform_remote
    try:
        raw = pd.read_csv(CONFIG.source_url)
        dataset = transform(raw)
        logger.info("Fetched ABS-style demographics from %s", CONFIG.source_url)
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("Falling back to synthetic ABS sample: %s", exc)
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
    fetch_abs()

