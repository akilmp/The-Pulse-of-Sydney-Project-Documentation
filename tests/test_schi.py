"""Tests for the SCHI computation helper."""

import pytest

from pulse.etl import load_cached_transport_data
from pulse.features import build_feature_matrix
from pulse.schi import compute_schi


def test_compute_schi_is_bounded() -> None:
    rows = load_cached_transport_data()
    features = build_feature_matrix(rows)
    score = compute_schi(features)
    assert 0.0 <= score <= 100.0


def test_compute_schi_penalises_large_delays() -> None:
    base_features = {
        "avg_delay_minutes": 1.0,
        "avg_mood_score": 5.0,
        "commute_observations": 3.0,
    }
    penalised_features = {**base_features, "avg_delay_minutes": 10.0}

    best_case = compute_schi(base_features)
    worst_case = compute_schi(penalised_features)

    assert worst_case < best_case


def test_compute_schi_handles_extreme_inputs() -> None:
    with pytest.raises(KeyError):
        compute_schi({})
