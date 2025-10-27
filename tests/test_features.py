"""Tests for feature engineering helpers."""

import pytest

from pulse.etl import load_cached_transport_data
from pulse.features import build_feature_matrix


def test_build_feature_matrix_summary_statistics() -> None:
    rows = load_cached_transport_data()
    features = build_feature_matrix(rows)

    assert features["commute_observations"] == pytest.approx(3.0)
    assert features["avg_delay_minutes"] == pytest.approx((5 + 0 + 2) / 3)
    assert features["avg_mood_score"] == pytest.approx((3 + 4 + 5) / 3)


def test_build_feature_matrix_requires_rows() -> None:
    with pytest.raises(ValueError):
        build_feature_matrix([])
