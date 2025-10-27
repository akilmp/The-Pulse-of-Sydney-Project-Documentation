from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from src.config import Settings


REQUIRED_COLUMNS = {
    "date",
    "sa2_code",
    "rainfall_mm",
    "temp_max_c",
    "temp_min_c",
}


def _load_weather_data(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(
            "Expected cleaned weather data at 'data/interim/weather_clean.csv'."
        )
    with path.open("r", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Weather dataset is missing required columns: {sorted(missing)}"
            )
        return [dict(row) for row in reader]


def _write_output(path: Path, records: List[Dict[str, object]]) -> None:
    fieldnames = ["sa2_code", "date", "rainfall_total_mm", "temp_mean_c", "temp_range_c"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            serialised = {**record}
            serialised["rainfall_total_mm"] = f"{record['rainfall_total_mm']:.3f}"
            serialised["temp_mean_c"] = f"{record['temp_mean_c']:.3f}"
            serialised["temp_range_c"] = f"{record['temp_range_c']:.3f}"
            writer.writerow(serialised)


def build_weather_features(settings: Settings | None = None) -> List[Dict[str, object]]:
    settings = settings or Settings()
    settings.ensure_directories()

    source = Path(settings.interim_dir) / "weather_clean.csv"
    rows = _load_weather_data(source)

    grouped: Dict[Tuple[str, str], List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (row["sa2_code"], row["date"])
        grouped[key].append(row)

    results: List[Dict[str, object]] = []
    for (sa2_code, date), items in sorted(grouped.items()):
        rainfall = [float(item["rainfall_mm"]) for item in items]
        temp_max = [float(item["temp_max_c"]) for item in items]
        temp_min = [float(item["temp_min_c"]) for item in items]

        total_rainfall = sum(rainfall)
        mean_temp = sum((hi + lo) / 2.0 for hi, lo in zip(temp_max, temp_min)) / len(items)
        mean_range = sum((hi - lo) for hi, lo in zip(temp_max, temp_min)) / len(items)

        results.append(
            {
                "sa2_code": sa2_code,
                "date": date,
                "rainfall_total_mm": round(total_rainfall, 3),
                "temp_mean_c": round(mean_temp, 3),
                "temp_range_c": round(mean_range, 3),
            }
        )

    output_path = Path(settings.processed_dir) / "weather_features.csv"
    _write_output(output_path, results)
    return results


def main() -> None:
    build_weather_features()


if __name__ == "__main__":
    main()
