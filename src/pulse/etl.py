"""Helpers that simulate ETL steps using committed fixtures."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "data" / "fixtures" / "transport_sample.csv"


def load_cached_transport_data(path: Path | None = None) -> List[Dict[str, str]]:
    """Load the cached transport dataset from ``data/fixtures``.

    Parameters
    ----------
    path:
        Optional override for the fixture path. Defaults to ``transport_sample.csv``.

    Returns
    -------
    list of dict
        Each dict represents one commute observation with ``date``, ``mode``,
        ``delay_minutes`` (stringified integer), and ``mood`` (stringified integer).
    """

    dataset_path = path or FIXTURE_PATH
    if not dataset_path.exists():
        raise FileNotFoundError(f"Fixture missing at {dataset_path}")

    with dataset_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        raise ValueError("The cached dataset is empty; supply at least one record.")

    expected_fields = {"date", "mode", "delay_minutes", "mood"}
    if set(reader.fieldnames or []) != expected_fields:
        raise ValueError(
            "Unexpected schema for cached transport data; "
            f"expected {sorted(expected_fields)}, got {reader.fieldnames}"
        )

    return rows
