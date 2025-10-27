"""Utility helpers for IO operations used across the ETL pipeline."""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import yaml

from .config import REGISTRY_PATH

logger = logging.getLogger(__name__)


def ensure_directory(path: Path) -> None:
    """Ensure that ``path``'s parent directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def sha256sum(path: Path) -> str:
    """Return the SHA-256 checksum for ``path``."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_registry() -> Dict[str, Dict[str, str]]:
    if REGISTRY_PATH.exists():
        with REGISTRY_PATH.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    return {}


def update_registry(dataset: str, metadata: Dict[str, str]) -> None:
    registry = load_registry()
    registry[dataset] = metadata
    with REGISTRY_PATH.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(registry, fh, sort_keys=True, allow_unicode=True)


def write_dataframe(df: pd.DataFrame, path: Path, *, index: bool = False) -> None:
    ensure_directory(path)
    df.to_csv(path, index=index)


def current_timestamp(tz: Optional[str] = 'UTC') -> str:
    from datetime import timezone

    tzinfo = None if tz is None else timezone.utc if tz.upper() == 'UTC' else None
    now = datetime.now(tz=tzinfo) if tzinfo else datetime.now().astimezone()
    return now.isoformat()


__all__ = [
    "ensure_directory",
    "sha256sum",
    "load_registry",
    "update_registry",
    "write_dataframe",
    "current_timestamp",
]

