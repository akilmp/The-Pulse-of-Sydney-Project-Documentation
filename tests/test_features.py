from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

from src.features.engineer_commute_features import build_commute_features
from src.features.engineer_weather_features import build_weather_features
from src.features.make_geometries import build_geometries
from tests.fixtures.pipeline import (
    DEFAULT_COMMUTE_ROWS,
    create_settings,
    seed_abs_tables,
    seed_commute_data,
    seed_weather_data,
)


def _hash_file(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def _index_by_key(rows: Iterable[dict[str, object]]) -> dict[tuple[str, str], dict[str, object]]:
    return {(row["sa2_code"], row["date"]): row for row in rows}


def test_feature_engineering_outputs_are_deterministic(tmp_path: Path) -> None:
    settings = create_settings(tmp_path)
    seed_abs_tables(settings)
    seed_commute_data(settings)
    seed_weather_data(settings)

    build_geometries(settings)
    first_commute = build_commute_features(settings)
    first_weather = build_weather_features(settings)

    commute_path = Path(settings.processed_dir) / "commute_features.csv"
    weather_path = Path(settings.processed_dir) / "weather_features.csv"

    first_commute_hash = _hash_file(commute_path)
    first_weather_hash = _hash_file(weather_path)

    # Run the feature engineering again to confirm deterministic output.
    second_commute = build_commute_features(settings)
    second_weather = build_weather_features(settings)

    assert first_commute == second_commute
    assert first_weather == second_weather
    assert first_commute_hash == _hash_file(commute_path)
    assert first_weather_hash == _hash_file(weather_path)

    commute_index = _index_by_key(first_commute)
    january_first = commute_index[("101021001", "2025-01-01")]
    assert january_first["avg_delay_min"] == 8.5
    assert january_first["severe_delay_share"] == 0.5
    assert january_first["trip_count"] == 2
    assert january_first["avg_mood"] == 3.5

    weather_index = _index_by_key(first_weather)
    january_weather = weather_index[("101021001", "2025-01-01")]
    assert january_weather["rainfall_total_mm"] == 2.0
    assert january_weather["temp_range_c"] == 10.5
    assert january_weather["temp_mean_c"] == 24.75


def test_weather_features_handle_all_zero_rainfall(tmp_path: Path) -> None:
    settings = create_settings(tmp_path)
    zero_rain_rows = [
        {
            "date": "2025-03-01",
            "sa2_code": "101021010",
            "rainfall_mm": 0.0,
            "temp_max_c": 21,
            "temp_min_c": 18,
        },
        {
            "date": "2025-03-01",
            "sa2_code": "101021010",
            "rainfall_mm": 0.0,
            "temp_max_c": 22,
            "temp_min_c": 17,
        },
    ]
    seed_weather_data(settings, rows=zero_rain_rows)

    results = build_weather_features(settings)
    weather_index = _index_by_key(results)
    march_weather = weather_index[("101021010", "2025-03-01")]

    assert march_weather["rainfall_total_mm"] == 0.0
    assert march_weather["temp_mean_c"] == 19.5
    assert march_weather["temp_range_c"] == 4.0

    # Ensure no other weather rows were written when starting from scratch.
    assert len(results) == 1


def test_commute_feature_aggregation_matches_expected(tmp_path: Path) -> None:
    settings = create_settings(tmp_path)
    seed_commute_data(settings, rows=DEFAULT_COMMUTE_ROWS)

    results = build_commute_features(settings)
    commute_index = _index_by_key(results)
    january_second = commute_index[("101021002", "2025-01-02")]

    assert january_second["avg_delay_min"] == 4.5
    assert january_second["trip_count"] == 2
    assert january_second["severe_delay_share"] == 0.0

    # Ensure the file on disk remains stable between runs.
    processed_path = Path(settings.processed_dir) / "commute_features.csv"
    first_hash = _hash_file(processed_path)
    build_commute_features(settings)
    assert _hash_file(processed_path) == first_hash
