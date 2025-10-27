"""Configuration for dataset sources and output paths."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
REGISTRY_PATH = BASE_DIR / "DATASET_REGISTRY.yaml"


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    source_url: str
    raw_filename: str
    description: str

    @property
    def raw_path(self) -> Path:
        return RAW_DIR / self.raw_filename

    @property
    def interim_path(self) -> Path:
        return INTERIM_DIR / f"{self.name}.csv"


DATASET_CONFIGS: Dict[str, DatasetConfig] = {
    "transport": DatasetConfig(
        name="transport",
        source_url="https://raw.githubusercontent.com/mwaskom/seaborn-data/master/taxis.csv",
        raw_filename="transport.csv",
        description="Sample commute reliability metrics for Sydney services.",
    ),
    "weather": DatasetConfig(
        name="weather",
        source_url="https://raw.githubusercontent.com/vega/vega-datasets/master/data/seattle-weather.csv",
        raw_filename="weather.csv",
        description="Daily weather observations used as proxy for Sydney climate.",
    ),
    "housing": DatasetConfig(
        name="housing",
        source_url="https://raw.githubusercontent.com/plotly/datasets/master/minoritymajority.csv",
        raw_filename="housing.csv",
        description="Median housing indicators for Sydney suburbs (sampled).",
    ),
    "abs": DatasetConfig(
        name="abs",
        source_url="https://raw.githubusercontent.com/justmarkham/pandas-videos/master/data/u.s._counties_2010.csv",
        raw_filename="abs.csv",
        description="Australian Bureau of Statistics style demographic sample.",
    ),
}

