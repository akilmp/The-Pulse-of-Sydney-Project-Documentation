"""Sydney Commute Happiness Index (SCHI) helpers."""

from __future__ import annotations

from typing import Mapping


def compute_schi(
    features: Mapping[str, float],
    delay_weight: float = 0.4,
    mood_weight: float = 0.6,
) -> float:
    """Compute a bounded SCHI score from engineered features.

    Parameters
    ----------
    features:
        Mapping containing ``avg_delay_minutes`` and ``avg_mood_score`` keys.
    delay_weight, mood_weight:
        Relative contribution of delay vs. mood (default weights favour mood).

    Returns
    -------
    float
        SCHI score clamped between 0 and 100.
    """

    avg_delay = float(features["avg_delay_minutes"])
    avg_mood = float(features["avg_mood_score"])

    raw_score = (mood_weight * (avg_mood / 5.0) * 100) - (delay_weight * avg_delay * 2)
    return max(0.0, min(100.0, raw_score))
