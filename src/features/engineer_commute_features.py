from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from src.config import Settings


REQUIRED_COLUMNS = {
    "date",
    "sa2_code",
    "observed_delay_min",
    "mood",
}


def _load_commute_data(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(
            "Expected cleaned commute data at 'data/interim/commute_clean.csv'."
        )
    with path.open("r", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Commute dataset is missing required columns: {sorted(missing)}"
            )
        return [dict(row) for row in reader]


def _write_output(path: Path, records: List[Dict[str, object]]) -> None:
    fieldnames = [
        "sa2_code",
        "date",
        "avg_delay_min",
        "severe_delay_share",
        "trip_count",
        "avg_mood",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            serialised = {**record}
            serialised["avg_delay_min"] = f"{record['avg_delay_min']:.3f}"
            serialised["severe_delay_share"] = f"{record['severe_delay_share']:.3f}"
            serialised["avg_mood"] = f"{record['avg_mood']:.3f}"
            serialised["trip_count"] = str(record["trip_count"])
            writer.writerow(serialised)


def build_commute_features(settings: Settings | None = None) -> List[Dict[str, object]]:
    settings = settings or Settings()
    settings.ensure_directories()

    source = Path(settings.interim_dir) / "commute_clean.csv"
    rows = _load_commute_data(source)

    grouped: Dict[Tuple[str, str], List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (row["sa2_code"], row["date"])
        grouped[key].append(row)

    results: List[Dict[str, object]] = []
    for (sa2_code, date), items in sorted(grouped.items()):
        delays = [float(item["observed_delay_min"]) for item in items]
        moods = [float(item["mood"]) for item in items]
        trip_count = len(items)
        severe_share = sum(delay >= 10 for delay in delays) / trip_count

        results.append(
            {
                "sa2_code": sa2_code,
                "date": date,
                "avg_delay_min": round(sum(delays) / trip_count, 3),
                "severe_delay_share": round(severe_share, 3),
                "trip_count": trip_count,
                "avg_mood": round(sum(moods) / trip_count, 3),
            }
        )

    output_path = Path(settings.processed_dir) / "commute_features.csv"
    _write_output(output_path, results)
    return results


def main() -> None:
    build_commute_features()


if __name__ == "__main__":
    main()
