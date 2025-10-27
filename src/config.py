"""Configuration helpers for the Sydney Pulse project."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


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


__all__ = ["ProjectConfig", "get_project_root", "load_config"]
