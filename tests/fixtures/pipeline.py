"""Utilities for building synthetic datasets used in tests."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from src.config import Settings

DEFAULT_ABS_ATTRIBUTES = [
    {"sa2_code": "101021001", "sa2_name": "Sydney Inner"},
    {"sa2_code": "101021002", "sa2_name": "Sydney Outer"},
]

DEFAULT_ABS_GEOMETRIES = [
    {
        "sa2_code": "101021001",
        "geometry_wkt": "POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))",
    },
    {
        "sa2_code": "101021002",
        "geometry_wkt": "POLYGON ((1 1, 2 1, 2 2, 1 2, 1 1))",
    },
]

DEFAULT_COMMUTE_ROWS = [
    {"date": "2025-01-01", "sa2_code": "101021001", "observed_delay_min": 5, "mood": 3},
    {"date": "2025-01-01", "sa2_code": "101021001", "observed_delay_min": 12, "mood": 4},
    {"date": "2025-01-02", "sa2_code": "101021002", "observed_delay_min": 3, "mood": 4},
    {"date": "2025-01-02", "sa2_code": "101021002", "observed_delay_min": 6, "mood": 5},
    {"date": "2025-01-03", "sa2_code": "101021001", "observed_delay_min": 6, "mood": 3},
    {"date": "2025-01-03", "sa2_code": "101021001", "observed_delay_min": 7, "mood": 4},
]

DEFAULT_WEATHER_ROWS = [
    {
        "date": "2025-01-01",
        "sa2_code": "101021001",
        "rainfall_mm": 2.0,
        "temp_max_c": 30,
        "temp_min_c": 20,
    },
    {
        "date": "2025-01-01",
        "sa2_code": "101021001",
        "rainfall_mm": 0.0,
        "temp_max_c": 30,
        "temp_min_c": 19,
    },
    {
        "date": "2025-01-02",
        "sa2_code": "101021002",
        "rainfall_mm": 0.5,
        "temp_max_c": 25,
        "temp_min_c": 18,
    },
    {
        "date": "2025-01-02",
        "sa2_code": "101021002",
        "rainfall_mm": 1.0,
        "temp_max_c": 24,
        "temp_min_c": 17,
    },
    {
        "date": "2025-01-03",
        "sa2_code": "101021001",
        "rainfall_mm": 1.0,
        "temp_max_c": 29,
        "temp_min_c": 20,
    },
    {
        "date": "2025-01-03",
        "sa2_code": "101021001",
        "rainfall_mm": 0.0,
        "temp_max_c": 28,
        "temp_min_c": 19,
    },
]


def create_settings(base_dir: Path, **kwargs: object) -> Settings:
    """Instantiate settings rooted at ``base_dir`` with ensured directories."""

    settings = Settings(base_dir=base_dir, **kwargs)
    settings.ensure_directories()
    return settings


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))


def seed_abs_tables(
    settings: Settings,
    attributes: Sequence[Mapping[str, object]] | None = None,
    geometries: Sequence[Mapping[str, object]] | None = None,
) -> None:
    interim_dir = Path(settings.interim_dir)
    _write_csv(
        interim_dir / "abs_sa2_attributes.csv",
        ["sa2_code", "sa2_name"],
        attributes or DEFAULT_ABS_ATTRIBUTES,
    )
    _write_csv(
        interim_dir / "abs_sa2_geometries.csv",
        ["sa2_code", "geometry_wkt"],
        geometries or DEFAULT_ABS_GEOMETRIES,
    )


def seed_commute_data(
    settings: Settings,
    rows: Sequence[Mapping[str, object]] | None = None,
) -> None:
    interim_dir = Path(settings.interim_dir)
    _write_csv(
        interim_dir / "commute_clean.csv",
        ["date", "sa2_code", "observed_delay_min", "mood"],
        rows or DEFAULT_COMMUTE_ROWS,
    )


def seed_weather_data(
    settings: Settings,
    rows: Sequence[Mapping[str, object]] | None = None,
) -> None:
    interim_dir = Path(settings.interim_dir)
    _write_csv(
        interim_dir / "weather_clean.csv",
        ["date", "sa2_code", "rainfall_mm", "temp_max_c", "temp_min_c"],
        rows or DEFAULT_WEATHER_ROWS,
    )


__all__ = [
    "DEFAULT_ABS_ATTRIBUTES",
    "DEFAULT_ABS_GEOMETRIES",
    "DEFAULT_COMMUTE_ROWS",
    "DEFAULT_WEATHER_ROWS",
    "create_settings",
    "seed_abs_tables",
    "seed_commute_data",
    "seed_weather_data",
]
