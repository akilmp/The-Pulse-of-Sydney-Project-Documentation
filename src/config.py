"""Configuration helpers for the Sydney Pulse project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping


@dataclass
class Settings:
    """Project configuration container.

    Parameters are intentionally lightweight so that unit tests can instantiate
    the settings object with a temporary base directory. All paths are resolved
    relative to :attr:`base_dir` unless explicitly provided.
    """

    base_dir: Path = Path(".")
    data_dir: Path | None = None
    raw_dir: Path | None = None
    interim_dir: Path | None = None
    processed_dir: Path | None = None
    schi_weights: Mapping[str, float] | None = None

    def __post_init__(self) -> None:
        self.base_dir = Path(self.base_dir)
        if self.data_dir is None:
            self.data_dir = self.base_dir / "data"
        else:
            self.data_dir = self._resolve(self.data_dir)

        if self.raw_dir is None:
            self.raw_dir = self.data_dir / "raw"
        else:
            self.raw_dir = self._resolve(self.raw_dir)

        if self.interim_dir is None:
            self.interim_dir = self.data_dir / "interim"
        else:
            self.interim_dir = self._resolve(self.interim_dir)

        if self.processed_dir is None:
            self.processed_dir = self.data_dir / "processed"
        else:
            self.processed_dir = self._resolve(self.processed_dir)

        if self.schi_weights is None:
            self.schi_weights = self._default_weights()
        else:
            self.schi_weights = self._normalize(self.schi_weights)

    @property
    def SCHI_WEIGHTS(self) -> Mapping[str, float]:
        return self.schi_weights

    def _resolve(self, path: Path | str) -> Path:
        path = Path(path)
        if path.is_absolute():
            return path
        return self.base_dir / path

    def _default_weights(self) -> Mapping[str, float]:
        weights: Dict[str, float] = {
            "reliability": 0.4,
            "mood": 0.3,
            "rain_comfort": 0.2,
            "temperature": 0.1,
        }
        return self._normalize(weights)

    @staticmethod
    def _normalize(weights: Mapping[str, float]) -> Mapping[str, float]:
        total = float(sum(weights.values()))
        if total == 0:
            raise ValueError("SCHI weights must sum to a positive value")
        return {key: float(value) / total for key, value in weights.items()}

    def ensure_directories(self) -> None:
        """Create data directories if they do not already exist."""

        for path in (self.raw_dir, self.interim_dir, self.processed_dir):
            Path(path).mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class DatasetConfig:
    """Metadata describing a dataset managed by the project."""

    name: str
    description: str
    source_url: str
    raw_path: Path
    interim_path: Path


def _data_subdir(*parts: str) -> Path:
    return Path("data").joinpath(*parts)


DATASET_CONFIGS: dict[str, DatasetConfig] = {
    "transport": DatasetConfig(
        name="transport",
        description="Sydney public transport data used for commute analysis.",
        source_url="https://opendata.transport.nsw.gov.au/",
        raw_path=_data_subdir("raw", "transport"),
        interim_path=_data_subdir("interim", "transport"),
    ),
    "weather": DatasetConfig(
        name="weather",
        description="Weather observations for Sydney used in feature engineering.",
        source_url="http://www.bom.gov.au/climate/data/",
        raw_path=_data_subdir("raw", "weather"),
        interim_path=_data_subdir("interim", "weather"),
    ),
    "housing": DatasetConfig(
        name="housing",
        description="Housing affordability and rental market indicators.",
        source_url="https://www.domain.com.au/research/",
        raw_path=_data_subdir("raw", "housing"),
        interim_path=_data_subdir("interim", "housing"),
    ),
    "abs": DatasetConfig(
        name="abs",
        description="Australian Bureau of Statistics releases relevant to the project.",
        source_url="https://www.abs.gov.au/",
        raw_path=_data_subdir("raw", "abs"),
        interim_path=_data_subdir("interim", "abs"),
    ),
}


__all__ = ["Settings", "DatasetConfig", "DATASET_CONFIGS"]

