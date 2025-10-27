"""Clean housing indicator data."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

import pandas as pd
from pandas import DataFrame

from ..config import DATASET_CONFIGS
from ..utils_io import write_dataframe
from .utils import canonicalize_area_name, ensure_columns, reorder_columns

logger = logging.getLogger(__name__)
CONFIG = DATASET_CONFIGS["housing"]
RAW_COLUMNS = ["sa2_name", "suburb", "median_sale_price", "median_rent", "observation_month"]
CLEAN_COLUMNS = [
    "sa2_name",
    "sa2_canonical",
    "suburb",
    "suburb_canonical",
    "observation_month",
    "median_sale_price",
    "median_rent",
    "price_to_rent_ratio",
]

SA2_ALIASES: Dict[str, str] = {
    "Sydney - Haymarket - The Rocks": "Sydney - Haymarket - The Rocks",
    "Sydney Cbd": "Sydney - Haymarket - The Rocks",
    "Parramatta - Rosehill": "Parramatta - Rosehill",
    "Randwick": "Randwick",
}


def enforce_schema(df: DataFrame) -> DataFrame:
    ensure_columns(df, CLEAN_COLUMNS)
    ordered = reorder_columns(df, CLEAN_COLUMNS)
    ordered["median_sale_price"] = pd.to_numeric(ordered["median_sale_price"], errors="coerce").fillna(0).round(0)
    ordered["median_rent"] = pd.to_numeric(ordered["median_rent"], errors="coerce").fillna(0).round(0)
    ordered["price_to_rent_ratio"] = pd.to_numeric(ordered["price_to_rent_ratio"], errors="coerce").fillna(0).round(2)
    ordered["observation_month"] = pd.to_datetime(ordered["observation_month"], errors="coerce")
    if ordered["observation_month"].isna().any():
        raise ValueError("observation_month contains nulls")
    return ordered


def clean_housing(raw_path: str | None = None, output_path: str | None = None) -> DataFrame:
    raw_path = raw_path or str(CONFIG.raw_path)
    output_path = output_path or str(CONFIG.interim_path)
    df = pd.read_csv(raw_path)
    ensure_columns(df, RAW_COLUMNS)

    suburb = df["suburb"].map(canonicalize_area_name)
    sa2_canonical = df["sa2_name"].map(SA2_ALIASES).fillna(df["sa2_name"]).str.title()

    observation_month = pd.to_datetime(df["observation_month"], errors="coerce")
    observation_month = observation_month.dt.to_period("M").dt.to_timestamp()

    sale_price = pd.to_numeric(df["median_sale_price"], errors="coerce").fillna(0)
    rent = pd.to_numeric(df["median_rent"], errors="coerce").fillna(0)
    denominator = (rent * 52).replace({0: pd.NA})
    price_to_rent = (sale_price / denominator).fillna(0)

    cleaned = pd.DataFrame(
        {
            "sa2_name": df["sa2_name"],
            "sa2_canonical": sa2_canonical,
            "suburb": df["suburb"],
            "suburb_canonical": suburb,
            "observation_month": observation_month,
            "median_sale_price": sale_price,
            "median_rent": rent,
            "price_to_rent_ratio": price_to_rent.round(2),
        }
    )

    cleaned = cleaned.dropna(subset=["observation_month", "suburb_canonical"])
    cleaned = enforce_schema(cleaned)
    write_dataframe(cleaned, Path(output_path))
    logger.info("Wrote cleaned housing data to %s", output_path)
    return cleaned


if __name__ == "__main__":
    clean_housing()

