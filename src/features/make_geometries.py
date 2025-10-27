from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List

from src.config import Settings


def _read_csv(path: Path, required_columns: Iterable[str]) -> List[dict[str, str]]:
    if not path.exists():
        missing = ", ".join(required_columns)
        raise FileNotFoundError(
            f"Expected '{path}' with columns [{missing}], but the file was not found."
        )
    with path.open("r", newline="") as handle:
        reader = csv.DictReader(handle)
        missing_cols = set(required_columns) - set(reader.fieldnames or [])
        if missing_cols:
            raise ValueError(
                f"File '{path}' is missing required columns: {sorted(missing_cols)}"
            )
        return [dict(row) for row in reader]


def build_geometries(settings: Settings | None = None) -> List[dict[str, str]]:
    """Join ABS geography tables and persist the combined geometries dataset."""

    settings = settings or Settings()
    settings.ensure_directories()

    attributes_path = Path(settings.interim_dir) / "abs_sa2_attributes.csv"
    geometries_path = Path(settings.interim_dir) / "abs_sa2_geometries.csv"

    attributes = _read_csv(attributes_path, ["sa2_code", "sa2_name"])
    geometries = _read_csv(geometries_path, ["sa2_code", "geometry_wkt"])

    attribute_map = {row["sa2_code"]: row for row in attributes}
    geometry_map = {row["sa2_code"]: row for row in geometries}

    combined_codes = sorted(set(attribute_map) & set(geometry_map))
    merged: List[dict[str, str]] = []
    for code in combined_codes:
        merged.append(
            {
                "sa2_code": code,
                "sa2_name": attribute_map[code].get("sa2_name", ""),
                "geometry_wkt": geometry_map[code].get("geometry_wkt", ""),
            }
        )

    output_path = Path(settings.processed_dir) / "sa2_geometries.csv"
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sa2_code", "sa2_name", "geometry_wkt"])
        writer.writeheader()
        writer.writerows(merged)

    return merged


def main() -> None:
    build_geometries()


if __name__ == "__main__":
    main()
