"""Feature engineering helpers derived from cached ETL output."""

from __future__ import annotations

from statistics import mean
from typing import Iterable, List

CommuteRow = dict[str, str]


def _to_float(values: Iterable[str]) -> List[float]:
    return [float(value) for value in values]


def build_feature_matrix(rows: Iterable[CommuteRow]) -> dict[str, float]:
    """Aggregate commute rows into a compact feature dictionary.

    The simplified feature set deliberately mirrors the documentation narrative by
    computing average delay, average mood, and a commute count that can feed the
    SCHI calculation.
    """

    rows = list(rows)
    if not rows:
        raise ValueError("No commute rows supplied for feature engineering.")

    delays = _to_float(row["delay_minutes"] for row in rows)
    moods = _to_float(row["mood"] for row in rows)

    return {
        "avg_delay_minutes": mean(delays),
        "avg_mood_score": mean(moods),
        "commute_observations": float(len(rows)),
    }
