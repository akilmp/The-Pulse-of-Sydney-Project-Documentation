"""Tests for the lightweight ETL helpers."""

from pathlib import Path

import pytest

from pulse.etl import FIXTURE_PATH, load_cached_transport_data


def test_load_cached_transport_data_reads_fixture(tmp_path: Path) -> None:
    rows = load_cached_transport_data()
    assert len(rows) == 3
    assert rows[0]["mode"] == "train"


def test_load_cached_transport_data_with_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.csv"
    with pytest.raises(FileNotFoundError):
        load_cached_transport_data(missing)


def test_fixture_schema_guard() -> None:
    rows = load_cached_transport_data()
    assert set(rows[0].keys()) == {"date", "mode", "delay_minutes", "mood"}
    assert FIXTURE_PATH.exists()
