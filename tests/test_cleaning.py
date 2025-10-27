from __future__ import annotations

import pandas as pd
import pytest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.cleaning.clean_abs import clean_abs
from src.cleaning.clean_housing import clean_housing
from src.cleaning.clean_transport import clean_transport, enforce_schema as transport_enforce_schema
from src.cleaning.utils import canonicalize_area_name


def test_canonicalize_area_name_normalises_aliases() -> None:
    assert canonicalize_area_name("  SYDNEY CBD  ") == "Sydney CBD"
    assert canonicalize_area_name("olympic park") == "Sydney Olympic Park"
    assert canonicalize_area_name("unknown suburb") == "Unknown Suburb"


def test_transport_enforce_schema_requires_columns() -> None:
    df = pd.DataFrame({"service_timestamp": [pd.Timestamp("2023-05-01T00:00:00Z")]})
    with pytest.raises(ValueError):
        transport_enforce_schema(df)


def test_clean_transport_drops_null_locations(tmp_path) -> None:
    raw = pd.DataFrame(
        {
            "record_id": [1, 2],
            "service_start": ["2023-05-01T07:30:00Z", "2023-05-01T08:00:00Z"],
            "service_end": ["2023-05-01T08:00:00Z", "2023-05-01T08:30:00Z"],
            "origin": ["Parramatta", None],
            "destination": ["Sydney CBD", "Randwick"],
            "mode": ["Train", "Bus"],
            "distance": [20, 5],
            "passengers": [300, 40],
            "total_fare": [6.2, 3.5],
        }
    )
    raw_path = tmp_path / "transport.csv"
    output_path = tmp_path / "transport_clean.csv"
    raw.to_csv(raw_path, index=False)
    cleaned = clean_transport(str(raw_path), output_path=str(output_path))
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["origin_suburb"] == "Parramatta"


def test_clean_housing_price_to_rent_ratio(tmp_path) -> None:
    raw = pd.DataFrame(
        {
            "sa2_name": ["Randwick"],
            "suburb": ["Randwick"],
            "median_sale_price": [1300000],
            "median_rent": [800],
            "observation_month": ["2023-05"],
        }
    )
    raw_path = tmp_path / "housing.csv"
    output_path = tmp_path / "housing_clean.csv"
    raw.to_csv(raw_path, index=False)
    cleaned = clean_housing(str(raw_path), output_path=str(output_path))
    expected_ratio = round(1300000 / (800 * 52), 2)
    assert pytest.approx(cleaned.iloc[0]["price_to_rent_ratio"], rel=1e-3) == expected_ratio


def test_clean_abs_population_bucket(tmp_path) -> None:
    raw = pd.DataFrame(
        {
            "sa2_code": ["117011321", "125021656"],
            "sa2_name": ["Sydney - Haymarket - The Rocks", "Parramatta - Rosehill"],
            "population": [15000, 52000],
            "median_age": [34, 35],
            "seifa_score": [1080, 1010],
        }
    )
    raw_path = tmp_path / "abs.csv"
    output_path = tmp_path / "abs_clean.csv"
    raw.to_csv(raw_path, index=False)
    cleaned = clean_abs(str(raw_path), output_path=str(output_path))
    assert cleaned.loc[cleaned["sa2_code"] == "117011321", "population_bucket"].iloc[0] == "small"
    assert cleaned.loc[cleaned["sa2_code"] == "125021656", "population_bucket"].iloc[0] == "large"

