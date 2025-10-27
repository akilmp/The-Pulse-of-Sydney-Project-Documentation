from __future__ import annotations

import csv
from pathlib import Path

from src.config import Settings
from src.features.composite_index import (
    build_composite_index,
    min_max_scale,
    min_max_scale_inverse,
)
from src.features.engineer_commute_features import build_commute_features
from src.features.engineer_weather_features import build_weather_features
from src.features.make_geometries import build_geometries


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _settings_with_data(tmp_path: Path) -> Settings:
    settings = Settings(base_dir=tmp_path)
    settings.ensure_directories()

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
            {"date": "2025-01-01", "sa2_code": "101021001", "observed_delay_min": 5, "mood": 4},
            {"date": "2025-01-01", "sa2_code": "101021001", "observed_delay_min": 7, "mood": 5},
            {"date": "2025-01-01", "sa2_code": "101021002", "observed_delay_min": 12, "mood": 3},
            {"date": "2025-01-01", "sa2_code": "101021002", "observed_delay_min": 15, "mood": 2},
        ],
    )
    _write_csv(
        interim / "weather_clean.csv",
        ["date", "sa2_code", "rainfall_mm", "temp_max_c", "temp_min_c"],
        [
            {"date": "2025-01-01", "sa2_code": "101021001", "rainfall_mm": 0.0, "temp_max_c": 28, "temp_min_c": 20},
            {"date": "2025-01-01", "sa2_code": "101021001", "rainfall_mm": 0.5, "temp_max_c": 27, "temp_min_c": 19},
            {"date": "2025-01-01", "sa2_code": "101021002", "rainfall_mm": 5.0, "temp_max_c": 30, "temp_min_c": 25},
            {"date": "2025-01-01", "sa2_code": "101021002", "rainfall_mm": 6.0, "temp_max_c": 31, "temp_min_c": 24},
        ],
    )

    build_geometries(settings)
    build_commute_features(settings)
    build_weather_features(settings)
    return settings


def test_min_max_scale_bounds() -> None:
    scaled = min_max_scale([1, 2, 3, 4])
    assert scaled[0] == 0.0
    assert scaled[-1] == 1.0

    inverse_scaled = min_max_scale_inverse([1, 2, 3, 4])
    assert inverse_scaled[0] == 1.0
    assert inverse_scaled[-1] == 0.0


def test_min_max_scale_handles_constant_series() -> None:
    scaled = min_max_scale([5, 5, 5])
    assert scaled == [0.0, 0.0, 0.0]


def test_composite_index_monotonic_with_delays(tmp_path: Path) -> None:
    settings = _settings_with_data(tmp_path)
    results = build_composite_index(settings)

    geometry_wkt_values = [row.get("geometry_wkt") for row in results]
    assert all(value for value in geometry_wkt_values)

    schi_values = [row["schi"] for row in results]
    assert all(0.0 <= value <= 1.0 for value in schi_values)

    # Two SA2 codes appear once each due to identical dates.
    lookup = {row["sa2_code"]: row for row in results}
    assert lookup["101021001"]["schi"] > lookup["101021002"]["schi"]

    # Increase delays for the low delay suburb and ensure the score drops.
    interim = Path(settings.interim_dir)
    with (interim / "commute_clean.csv").open("r", newline="") as handle:
        reader = list(csv.DictReader(handle))

    for row in reader:
        if row["sa2_code"] == "101021001":
            row["observed_delay_min"] = str(float(row["observed_delay_min"]) + 20)

    _write_csv(
        interim / "commute_clean.csv",
        ["date", "sa2_code", "observed_delay_min", "mood"],
        reader,
    )

    build_commute_features(settings)
    downgraded = build_composite_index(settings)

    new_lookup = {row["sa2_code"]: row for row in downgraded}
    assert new_lookup["101021001"]["schi"] + 1e-6 < lookup["101021001"]["schi"]
