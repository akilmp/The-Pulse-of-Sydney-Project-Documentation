from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.features.composite_index import (
    build_composite_index,
    min_max_scale,
    min_max_scale_inverse,
)
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


@pytest.fixture
def seeded_settings(tmp_path: Path):
    settings = create_settings(tmp_path)
    seed_abs_tables(settings)
    seed_commute_data(settings)
    seed_weather_data(settings)
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


def test_settings_normalizes_schi_weights(tmp_path: Path) -> None:
    raw_weights = {"reliability": 2, "mood": 2, "rain_comfort": 1, "temperature": 1}
    settings = create_settings(tmp_path, schi_weights=raw_weights)

    total = sum(settings.SCHI_WEIGHTS.values())
    assert pytest.approx(total, rel=1e-6) == 1.0
    assert settings.SCHI_WEIGHTS["reliability"] == pytest.approx(1 / 3)
    assert settings.SCHI_WEIGHTS["temperature"] == pytest.approx(1 / 6)


def test_composite_index_joins_geometries(seeded_settings) -> None:
    results = build_composite_index(seeded_settings)

    assert all(row["geometry_wkt"] for row in results)
    assert all(0.0 <= row["schi"] <= 1.0 for row in results)

    processed_path = Path(seeded_settings.processed_dir) / "schi.csv"
    with processed_path.open("r", newline="") as handle:
        reader = csv.DictReader(handle)
        assert set(reader.fieldnames or []) >= {"schi", "geometry_wkt"}


def test_composite_index_score_decreases_with_higher_delays(seeded_settings) -> None:
    baseline = build_composite_index(seeded_settings)
    lookup = {row["sa2_code"]: row for row in baseline}

    worse_commute_rows = []
    for row in DEFAULT_COMMUTE_ROWS:
        if row["sa2_code"] == "101021001" and row["date"] == "2025-01-03":
            updated = {**row, "observed_delay_min": row["observed_delay_min"] + 30}
            worse_commute_rows.append(updated)
        else:
            worse_commute_rows.append(dict(row))

    seed_commute_data(seeded_settings, rows=worse_commute_rows)
    build_commute_features(seeded_settings)

    downgraded = build_composite_index(seeded_settings)
    new_lookup = {row["sa2_code"]: row for row in downgraded}

    assert new_lookup["101021001"]["schi"] < lookup["101021001"]["schi"]
    assert new_lookup["101021002"]["schi"] == pytest.approx(
        lookup["101021002"]["schi"], rel=1e-6
    )


__all__ = [
    "test_min_max_scale_bounds",
    "test_min_max_scale_handles_constant_series",
    "test_settings_normalizes_schi_weights",
    "test_composite_index_joins_geometries",
    "test_composite_index_score_decreases_with_higher_delays",
]
