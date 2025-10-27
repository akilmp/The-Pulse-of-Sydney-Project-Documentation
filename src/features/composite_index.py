from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Iterable, List, Mapping

from src.config import Settings


def min_max_scale(values: Iterable[float]) -> List[float]:
    """Scale values to the ``[0, 1]`` interval with deterministic behaviour."""

    values_list = [float(value) for value in values]
    if not values_list:
        return []

    finite_values = [value for value in values_list if math.isfinite(value)]
    if not finite_values:
        return [0.0 for _ in values_list]

    min_val = min(finite_values)
    max_val = max(finite_values)
    if math.isclose(min_val, max_val):
        return [0.0 for _ in values_list]

    scale = max_val - min_val
    return [max(0.0, min(1.0, (value - min_val) / scale)) for value in values_list]


def min_max_scale_inverse(values: Iterable[float]) -> List[float]:
    """Inverse the :func:`min_max_scale` transformation."""

    return [1.0 - value for value in min_max_scale(values)]


def _load_processed(name: str, settings: Settings) -> List[dict[str, str]]:
    path = Path(settings.processed_dir) / name
    if not path.exists():
        raise FileNotFoundError(f"Expected processed dataset at '{path}'.")
    with path.open("r", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _write_output(path: Path, fieldnames: List[str], rows: List[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            serialised: dict[str, object] = {}
            for key in fieldnames:
                value = row.get(key)
                if isinstance(value, float):
                    if key == "schi":
                        serialised[key] = f"{value:.4f}"
                    else:
                        serialised[key] = f"{value:.3f}"
                else:
                    serialised[key] = value
            writer.writerow(serialised)


def _merge_features(
    commute: List[dict[str, str]],
    weather: List[dict[str, str]],
) -> List[dict[str, object]]:
    commute_map = {(row["sa2_code"], row["date"]): row for row in commute}
    weather_map = {(row["sa2_code"], row["date"]): row for row in weather}

    merged: List[dict[str, object]] = []
    for key in sorted(set(commute_map) & set(weather_map)):
        commute_row = commute_map[key]
        weather_row = weather_map[key]
        combined: dict[str, object] = {
            "sa2_code": key[0],
            "date": key[1],
        }
        combined.update(
            {
                "avg_delay_min": float(commute_row["avg_delay_min"]),
                "severe_delay_share": float(commute_row["severe_delay_share"]),
                "trip_count": int(float(commute_row["trip_count"])),
                "avg_mood": float(commute_row["avg_mood"]),
                "rainfall_total_mm": float(weather_row["rainfall_total_mm"]),
                "temp_mean_c": float(weather_row["temp_mean_c"]),
                "temp_range_c": float(weather_row["temp_range_c"]),
            }
        )
        merged.append(combined)
    return merged


def _apply_weights(rows: List[dict[str, object]], weights: Mapping[str, float]) -> None:
    required = {"reliability", "mood", "rain_comfort", "temperature"}
    missing = required - set(weights)
    if missing:
        raise KeyError(f"SCHI weights missing keys: {sorted(missing)}")

    reliability_scores = min_max_scale_inverse(row["avg_delay_min"] for row in rows)
    mood_scores = min_max_scale(row["avg_mood"] for row in rows)
    rain_scores = min_max_scale_inverse(row["rainfall_total_mm"] for row in rows)
    temp_scores = min_max_scale_inverse(abs(row["temp_range_c"]) for row in rows)

    for row, reliability, mood, rain, temp in zip(
        rows, reliability_scores, mood_scores, rain_scores, temp_scores
    ):
        row["reliability_score"] = reliability
        row["mood_score"] = mood
        row["rain_comfort_score"] = rain
        row["temperature_score"] = temp
        row["schi"] = round(
            reliability * weights["reliability"]
            + mood * weights["mood"]
            + rain * weights["rain_comfort"]
            + temp * weights["temperature"],
            4,
        )


def build_composite_index(settings: Settings | None = None) -> List[dict[str, object]]:
    settings = settings or Settings()
    settings.ensure_directories()

    commute = _load_processed("commute_features.csv", settings)
    weather = _load_processed("weather_features.csv", settings)
    geometries = _load_processed("sa2_geometries.csv", settings)
    geometry_map = {row["sa2_code"]: row.get("geometry_wkt", "") for row in geometries}

    merged = _merge_features(commute, weather)
    _apply_weights(merged, settings.SCHI_WEIGHTS)

    for row in merged:
        row["geometry_wkt"] = geometry_map.get(row["sa2_code"], "")

    merged.sort(key=lambda item: (item["sa2_code"], item["date"]))

    fieldnames = [
        "sa2_code",
        "date",
        "avg_delay_min",
        "severe_delay_share",
        "trip_count",
        "avg_mood",
        "rainfall_total_mm",
        "temp_mean_c",
        "temp_range_c",
        "reliability_score",
        "mood_score",
        "rain_comfort_score",
        "temperature_score",
        "schi",
        "geometry_wkt",
    ]

    output_path = Path(settings.processed_dir) / "schi.csv"
    _write_output(output_path, fieldnames, merged)
    return merged


def main() -> None:
    build_composite_index()


if __name__ == "__main__":
    main()
