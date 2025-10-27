from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.cleaning.clean_abs import CLEAN_COLUMNS as ABS_COLUMNS, clean_abs
from src.cleaning.clean_housing import CLEAN_COLUMNS as HOUSING_COLUMNS, clean_housing
from src.cleaning.clean_transport import CLEAN_COLUMNS as TRANSPORT_COLUMNS, clean_transport
from src.cleaning.clean_weather import CLEAN_COLUMNS as WEATHER_COLUMNS, clean_weather


@pytest.fixture
def raw_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "raw"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@pytest.fixture
def interim_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "interim"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_clean_transport_enforces_schema(raw_dir: Path, interim_dir: Path) -> None:
    raw_path = raw_dir / "transport.csv"
    output_path = interim_dir / "transport_clean.csv"
    rows = [
        {
            "record_id": 1,
            "service_start": "2025-01-01T08:00:00Z",
            "service_end": "2025-01-01T08:45:00Z",
            "origin": "Sydney CBD",
            "destination": "Parramatta",
            "mode": "bus",
            "distance": 5,
            "passengers": 160,
            "total_fare": 123.45,
        },
        {
            "record_id": 2,
            "service_start": "2025-01-01T09:00:00Z",
            "service_end": "2025-01-01T12:00:00Z",
            "origin": "Chatswood",
            "destination": "Sydney Olympic Park",
            "mode": "train",
            "distance": 25,
            "passengers": 400,
            "total_fare": 987.65,
        },
    ]
    _write_csv(
        raw_path,
        [
            "record_id",
            "service_start",
            "service_end",
            "origin",
            "destination",
            "mode",
            "distance",
            "passengers",
            "total_fare",
        ],
        rows,
    )

    cleaned = clean_transport(str(raw_path), str(output_path))

    assert list(cleaned.columns) == TRANSPORT_COLUMNS
    assert not cleaned["service_timestamp"].isna().any()
    assert "Australia/Sydney" in str(cleaned["service_timestamp"].dtype)
    assert (cleaned["delay_minutes"] >= 0).all()
    assert cleaned.loc[cleaned["service_id"] == 2, "status"].iloc[0] == "delayed"
    assert cleaned["load_factor"].between(0, 1).all()
    assert Path(output_path).exists()


def test_clean_weather_normalises_observations(raw_dir: Path, interim_dir: Path) -> None:
    raw_path = raw_dir / "weather.csv"
    output_path = interim_dir / "weather_clean.csv"
    rows = [
        {
            "observation_time": "2025-02-01T00:00:00Z",
            "rain_mm": -3,
            "temp_max_c": 28,
            "temp_min_c": 18,
            "observation_type": "Rain",
            "station_name": "Sydney Central",
            "suburb": "sydney cbd",
        },
        {
            "observation_time": "2025-02-01T01:00:00Z",
            "rain_mm": 2,
            "temp_max_c": 27,
            "temp_min_c": 19,
            "observation_type": "Sun",
            "station_name": "Sydney Central",
            "suburb": "Parramatta",
        },
        {
            "observation_time": "2025-02-01T01:00:00Z",
            "rain_mm": 2,
            "temp_max_c": 27,
            "temp_min_c": 19,
            "observation_type": "Sun",
            "station_name": "Sydney Central",
            "suburb": "Parramatta",
        },
    ]
    _write_csv(
        raw_path,
        [
            "observation_time",
            "rain_mm",
            "temp_max_c",
            "temp_min_c",
            "observation_type",
            "station_name",
            "suburb",
        ],
        rows,
    )

    cleaned = clean_weather(str(raw_path), str(output_path))

    assert list(cleaned.columns) == WEATHER_COLUMNS
    assert cleaned.shape[0] == 2  # duplicates removed
    assert (cleaned["rain_mm"] >= 0).all()
    first_row = cleaned.iloc[0]
    assert first_row["suburb"] == "Sydney CBD"
    assert first_row["weather_condition"] == "rain"
    assert "Australia/Sydney" in str(cleaned["observation_time"].dtype)
    assert Path(output_path).exists()


def test_clean_abs_buckets_population(raw_dir: Path, interim_dir: Path) -> None:
    raw_path = raw_dir / "abs.csv"
    output_path = interim_dir / "abs_clean.csv"
    rows = [
        {
            "sa2_code": "101021001",
            "sa2_name": "Sydney - Haymarket - The Rocks",
            "population": 15000,
            "median_age": 32,
            "seifa_score": 1010,
        },
        {
            "sa2_code": "101021002",
            "sa2_name": "Randwick",
            "population": 52000,
            "median_age": 38,
            "seifa_score": 990,
        },
    ]
    _write_csv(
        raw_path,
        ["sa2_code", "sa2_name", "population", "median_age", "seifa_score"],
        rows,
    )

    cleaned = clean_abs(str(raw_path), str(output_path))

    assert list(cleaned.columns) == ABS_COLUMNS
    assert cleaned.iloc[0]["population_bucket"] == "small"
    assert cleaned.iloc[1]["population_bucket"] == "large"
    assert cleaned.iloc[0]["sa2_canonical"] == "Sydney - Haymarket - The Rocks"
    assert Path(output_path).exists()


def test_clean_housing_computes_ratio(raw_dir: Path, interim_dir: Path) -> None:
    raw_path = raw_dir / "housing.csv"
    output_path = interim_dir / "housing_clean.csv"
    rows = [
        {
            "sa2_name": "Sydney Cbd",
            "suburb": "sydney cbd",
            "median_sale_price": 1_000_000,
            "median_rent": 800,
            "observation_month": "2025-01-15",
        },
        {
            "sa2_name": "Parramatta - Rosehill",
            "suburb": "Parramatta",
            "median_sale_price": 700_000,
            "median_rent": 600,
            "observation_month": "2025-01-20",
        },
    ]
    _write_csv(
        raw_path,
        [
            "sa2_name",
            "suburb",
            "median_sale_price",
            "median_rent",
            "observation_month",
        ],
        rows,
    )

    cleaned = clean_housing(str(raw_path), str(output_path))

    assert list(cleaned.columns) == HOUSING_COLUMNS
    first_row = cleaned.iloc[0]
    assert first_row["price_to_rent_ratio"] == pytest.approx(24.04, rel=1e-2)
    assert first_row["sa2_canonical"] == "Sydney - Haymarket - The Rocks"
    assert first_row["observation_month"].day == 1
    assert Path(output_path).exists()
