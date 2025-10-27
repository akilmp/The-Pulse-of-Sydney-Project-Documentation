"""Tests for the utility helpers in :mod:`src.utils_io`."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pandas as pd
import pytest
import yaml

from src import utils_io


def test_write_dataframe_and_checksum(tmp_path: Path) -> None:
    frame = pd.DataFrame({"alpha": [1, 2], "beta": ["x", "y"]})
    target = tmp_path / "exports" / "sample.csv"

    result = utils_io.write_dataframe(frame, target)

    assert result == target
    assert target.exists()
    text = target.read_text(encoding="utf-8")
    assert "alpha" in text and "beta" in text

    expected_checksum = utils_io.sha256sum(target)
    assert len(expected_checksum) == 64
    # sanity check that checksum changes if the file changes
    target.write_text("different", encoding="utf-8")
    assert utils_io.sha256sum(target) != expected_checksum


def test_update_registry_writes_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    registry_path = tmp_path / "registry" / "DATASET_REGISTRY.yaml"
    monkeypatch.setattr(utils_io, "_resolve_registry_path", lambda path=None: registry_path)

    metadata = {"dataset": "demo", "rows": 2, "columns": ["alpha", "beta"]}
    utils_io.update_registry("demo", metadata)

    contents = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    assert contents["demo"] == metadata

    extra = {"dataset": "demo", "rows": 3, "columns": ["alpha", "beta"], "note": "updated"}
    utils_io.update_registry("demo", extra)

    contents = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    assert contents["demo"] == extra


def test_fetch_weather_integration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYDNEY_PULSE_TIMEZONE", "UTC")

    registry_path = tmp_path / "registry.yaml"
    monkeypatch.setattr(utils_io, "_resolve_registry_path", lambda path=None: registry_path)

    raw_path = tmp_path / "data" / "raw" / "weather.csv"

    config_module = types.ModuleType("src.config")
    config_module.DATASET_CONFIGS = {
        "weather": types.SimpleNamespace(
            name="weather",
            description="Integration test dataset",
            source_url="https://example.com/weather.csv",
            raw_path=raw_path,
        )
    }
    monkeypatch.setitem(sys.modules, "src.config", config_module)
    monkeypatch.delitem(sys.modules, "src.etl.fetch_weather", raising=False)

    weather_module = importlib.import_module("src.etl.fetch_weather")

    sample = pd.DataFrame(
        {
            "date": ["2024-01-01"],
            "precipitation": [0.0],
            "temp_max": [25.0],
            "temp_min": [18.0],
            "weather": ["clear"],
        }
    )
    monkeypatch.setattr(weather_module.pd, "read_csv", lambda url: sample)

    output = weather_module.fetch_weather()

    assert Path(output) == raw_path
    assert raw_path.exists()

    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    assert "weather" in registry
    entry = registry["weather"]
    assert entry["dataset"] == "weather"
    assert entry["path"] == str(raw_path)
    assert entry["checksum"] == utils_io.sha256sum(raw_path)
