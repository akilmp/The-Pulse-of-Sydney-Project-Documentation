from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Iterable, List

from src.config import Settings
from src.features.engineer_commute_features import build_commute_features
from src.features.engineer_weather_features import build_weather_features
from src.features.make_geometries import build_geometries


def _hash_file(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def _create_base_settings(tmp_path: Path) -> Settings:
    settings = Settings(base_dir=tmp_path)
    settings.ensure_directories()
    return settings


def _write_csv(path: Path, fieldnames: Iterable[str], rows: List[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


def _prepare_inputs(settings: Settings) -> None:
    interim = Path(settings.interim_dir)

    _write_csv(
        interim / "abs_sa2_attributes.csv",
        ["sa2_code", "sa2_name"],
        [
            {"sa2_code": "101021001", "sa2_name": "Sydney Inner"},
            {"sa2_code": "101021002", "sa2_name": "Sydney Outer"},
        ],
    )

    _write_csv(
        interim / "abs_sa2_geometries.csv",
        ["sa2_code", "geometry_wkt"],
        [
            {
                "sa2_code": "101021001",
                "geometry_wkt": "POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))",
            },
            {
                "sa2_code": "101021002",
                "geometry_wkt": "POLYGON ((1 1, 2 1, 2 2, 1 2, 1 1))",
            },
        ],
    )

    _write_csv(
        interim / "commute_clean.csv",
        ["date", "sa2_code", "observed_delay_min", "mood"],
        [
            {"date": "2025-01-01", "sa2_code": "101021001", "observed_delay_min": 5, "mood": 3},
            {"date": "2025-01-01", "sa2_code": "101021001", "observed_delay_min": 12, "mood": 4},
            {"date": "2025-01-02", "sa2_code": "101021002", "observed_delay_min": 3, "mood": 4},
            {"date": "2025-01-02", "sa2_code": "101021002", "observed_delay_min": 6, "mood": 5},
        ],
    )

    _write_csv(
        interim / "weather_clean.csv",
        ["date", "sa2_code", "rainfall_mm", "temp_max_c", "temp_min_c"],
        [
            {"date": "2025-01-01", "sa2_code": "101021001", "rainfall_mm": 2.0, "temp_max_c": 30, "temp_min_c": 20},
            {"date": "2025-01-01", "sa2_code": "101021001", "rainfall_mm": 0.0, "temp_max_c": 30, "temp_min_c": 19},
            {"date": "2025-01-02", "sa2_code": "101021002", "rainfall_mm": 0.5, "temp_max_c": 25, "temp_min_c": 18},
            {"date": "2025-01-02", "sa2_code": "101021002", "rainfall_mm": 1.0, "temp_max_c": 24, "temp_min_c": 17},
        ],
    )


def _index_by_key(rows: List[dict[str, object]]) -> dict[tuple[str, str], dict[str, object]]:
    return {(row["sa2_code"], row["date"]): row for row in rows}


def test_feature_engineering_outputs_are_deterministic(tmp_path: Path) -> None:
    settings = _create_base_settings(tmp_path)
    _prepare_inputs(settings)

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
