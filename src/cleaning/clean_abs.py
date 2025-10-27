"""Clean ABS-style demographic data."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

import pandas as pd
from pandas import DataFrame

from ..config import DATASET_CONFIGS
from ..utils_io import write_dataframe
from .utils import ensure_columns, reorder_columns

logger = logging.getLogger(__name__)
CONFIG = DATASET_CONFIGS["abs"]
RAW_COLUMNS = ["sa2_code", "sa2_name", "population", "median_age", "seifa_score"]
CLEAN_COLUMNS = [
    "sa2_code",
    "sa2_name",
    "sa2_canonical",
    "population",
    "median_age",
    "seifa_score",
    "population_bucket",
]

SA2_ALIASES: Dict[str, str] = {
    "Sydney - Haymarket - The Rocks": "Sydney - Haymarket - The Rocks",
    "Parramatta - Rosehill": "Parramatta - Rosehill",
    "Randwick": "Randwick",
}


def enforce_schema(df: DataFrame) -> DataFrame:
    ensure_columns(df, CLEAN_COLUMNS)
    ordered = reorder_columns(df, CLEAN_COLUMNS)
    ordered["sa2_code"] = ordered["sa2_code"].astype(str)
    ordered["population"] = pd.to_numeric(ordered["population"], errors="coerce").fillna(0).astype(int)
    ordered["median_age"] = pd.to_numeric(ordered["median_age"], errors="coerce").fillna(0).round(1)
    ordered["seifa_score"] = pd.to_numeric(ordered["seifa_score"], errors="coerce").fillna(0).round(0)
    if ordered["sa2_code"].str.lower().eq("nan").any() or ordered["sa2_code"].str.strip().eq("").any():
        raise ValueError("sa2_code contains nulls")
    return ordered


def _population_bucket(pop: float) -> str:
    if pd.isna(pop):
        return "unknown"
    if pop < 20000:
        return "small"
    if pop < 50000:
        return "medium"
    return "large"


def clean_abs(raw_path: str | None = None, output_path: str | None = None) -> DataFrame:
    raw_path = raw_path or str(CONFIG.raw_path)
    output_path = output_path or str(CONFIG.interim_path)
    df = pd.read_csv(raw_path)
    ensure_columns(df, RAW_COLUMNS)

    sa2_name = df["sa2_name"].fillna("").apply(lambda x: x.strip()).replace("", pd.NA)
    canonical = sa2_name.map(SA2_ALIASES).fillna(sa2_name)

    population = pd.to_numeric(df["population"], errors="coerce")
    buckets = population.map(_population_bucket)

    cleaned = pd.DataFrame(
        {
            "sa2_code": df["sa2_code"],
            "sa2_name": sa2_name,
            "sa2_canonical": canonical,
            "population": population,
            "median_age": pd.to_numeric(df["median_age"], errors="coerce"),
            "seifa_score": pd.to_numeric(df["seifa_score"], errors="coerce"),
            "population_bucket": buckets,
        }
    )

    cleaned = cleaned.dropna(subset=["sa2_code", "sa2_canonical"])
    cleaned = enforce_schema(cleaned)
    write_dataframe(cleaned, Path(output_path))
    logger.info("Wrote cleaned ABS data to %s", output_path)
    return cleaned


if __name__ == "__main__":
    clean_abs()

