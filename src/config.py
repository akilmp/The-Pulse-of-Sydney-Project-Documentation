"""Configuration helpers for the Sydney Pulse project."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping, Optional

from dotenv import load_dotenv


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
        self.data_dir = self._resolve_or_default(self.data_dir, self.base_dir / "data")
        self.raw_dir = self._resolve_or_default(self.raw_dir, self.data_dir / "raw")
        self.interim_dir = self._resolve_or_default(self.interim_dir, self.data_dir / "interim")
        self.processed_dir = self._resolve_or_default(self.processed_dir, self.data_dir / "processed")

        if self.schi_weights is None:
            self.schi_weights = self._default_weights()
        else:
            self.schi_weights = self._normalize(self.schi_weights)

    @property
    def SCHI_WEIGHTS(self) -> Mapping[str, float]:
        return self.schi_weights

    def _resolve_or_default(self, value: Path | str | None, default: Path) -> Path:
        if value is None:
            return Path(default)
        return self._resolve(value)

    def _resolve(self, path: Path | str) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        return self.base_dir / candidate

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


__all__ = [
    "Settings",
    "ProjectConfig",
    "get_project_root",
    "load_config",
]
