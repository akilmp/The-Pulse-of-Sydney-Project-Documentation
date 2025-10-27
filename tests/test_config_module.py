"""Tests for the consolidated configuration module."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config import DATASET_CONFIGS, DatasetConfig, Settings


def test_settings_instantiation(tmp_path: Path) -> None:
    settings = Settings(base_dir=tmp_path)

    assert settings.base_dir == tmp_path
    assert settings.data_dir == tmp_path / "data"
    assert settings.raw_dir == tmp_path / "data" / "raw"
    assert settings.interim_dir == tmp_path / "data" / "interim"
    assert settings.processed_dir == tmp_path / "data" / "processed"
    assert pytest.approx(sum(settings.SCHI_WEIGHTS.values())) == 1.0


@pytest.mark.parametrize("dataset_name", sorted(DATASET_CONFIGS))
def test_dataset_configs_are_well_defined(dataset_name: str) -> None:
    config = DATASET_CONFIGS[dataset_name]

    assert isinstance(config, DatasetConfig)
    assert config.name == dataset_name
    assert config.raw_path.parts[:1] == ("data",)
    assert config.interim_path.parts[:1] == ("data",)

