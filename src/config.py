"""Configuration helpers for the Sydney Pulse project."""
from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Dict, Mapping, Optional

if importlib.util.find_spec("dotenv") is not None:  # pragma: no cover - optional
    load_dotenv = import_module("dotenv").load_dotenv
else:  # pragma: no cover - optional dependency missing
    def load_dotenv(*args: object, **kwargs: object) -> bool:
        return False


@dataclass(frozen=True)
class DatasetConfig:
    """Configuration describing storage locations and metadata for a dataset."""

    name: str
    description: str
    source_url: str
    raw_path: Path
    interim_path: Path
    processed_path: Path


def _dataset_paths(base_dir: Path, name: str) -> tuple[Path, Path, Path]:
    data_dir = base_dir / "data"
    raw = data_dir / "raw" / f"{name}.csv"
    interim = data_dir / "interim" / f"{name}_clean.csv"
    processed = data_dir / "processed" / f"{name}.csv"
    return raw, interim, processed


def _build_dataset_configs(base_dir: Path) -> Mapping[str, DatasetConfig]:
    descriptions = {
        "abs": (
            "Australian Bureau of Statistics style demographic sample.",
            "https://raw.githubusercontent.com/justmarkham/pandas-videos/master/data/u.s._counties_2010.csv",
        ),
        "housing": (
            "Median housing indicators for Sydney suburbs (sampled).",
            "https://raw.githubusercontent.com/plotly/datasets/master/minoritymajority.csv",
        ),
        "transport": (
            "Sample commute reliability metrics for Sydney services.",
            "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/taxis.csv",
        ),
        "weather": (
            "Daily weather observations used as proxy for Sydney climate.",
            "https://raw.githubusercontent.com/vega/vega-datasets/master/data/seattle-weather.csv",
        ),
    }

    configs: Dict[str, DatasetConfig] = {}
    for dataset, (description, source) in descriptions.items():
        raw_path, interim_path, processed_path = _dataset_paths(base_dir, dataset)
        configs[dataset] = DatasetConfig(
            name=dataset,
            description=description,
            source_url=source,
            raw_path=raw_path,
            interim_path=interim_path,
            processed_path=processed_path,
        )
    return configs


@dataclass
class Settings:
    """Project configuration container used throughout feature engineering."""

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
class ProjectConfig:
    """Base configuration values loaded from environment variables."""

    project_root: Path
    data_dir: Path
    raw_data_dir: Path
    interim_data_dir: Path
    processed_data_dir: Path
    timezone: str
    personal_log: Path
    default_cache_dir: Path
    env: str


def _load_env_file(dotenv_path: Optional[Path] = None) -> None:
    """Load environment variables from a .env file if it exists."""

    if dotenv_path is None:
        dotenv_path = Path.cwd() / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path, override=False)


def get_project_root() -> Path:
    """Return the absolute path to the repository root."""

    return Path(__file__).resolve().parents[1]


def load_config(env_file: Optional[Path] = None) -> ProjectConfig:
    """Create a :class:`ProjectConfig` from environment variables."""

    _load_env_file(env_file)

    project_root = get_project_root()
    data_dir = project_root / "data"

    timezone = os.getenv("SYDNEY_PULSE_TIMEZONE", "Australia/Sydney")
    env = os.getenv("SYDNEY_PULSE_ENV", "development")

    return ProjectConfig(
        project_root=project_root,
        data_dir=data_dir,
        raw_data_dir=data_dir / "raw",
        interim_data_dir=data_dir / "interim",
        processed_data_dir=data_dir / "processed",
        timezone=timezone,
        personal_log=data_dir / "raw" / "personal_commute_log.csv",
        default_cache_dir=project_root / "data" / "cache",
        env=env,
    )


PROJECT_ROOT = get_project_root()
DATASET_CONFIGS: Mapping[str, DatasetConfig] = _build_dataset_configs(PROJECT_ROOT)


__all__ = [
    "DatasetConfig",
    "DATASET_CONFIGS",
    "ProjectConfig",
    "Settings",
    "get_project_root",
    "load_config",
]
