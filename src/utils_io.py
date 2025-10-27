"""I/O utilities shared across the Sydney Pulse project."""

from __future__ import annotations

import csv
import hashlib
import os
from datetime import datetime, time
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Sequence, TYPE_CHECKING

import yaml
from pandas import DataFrame
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "Australia/Sydney"
DATASET_REGISTRY_ENV = "SYDNEY_PULSE_DATASET_REGISTRY"


if TYPE_CHECKING:  # pragma: no cover - type checking only
    import pandas as pd


def ensure_directory(path: Path) -> Path:
    """Ensure that the directory for ``path`` exists and return it."""

    directory = path if path.is_dir() else path.parent
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def current_timestamp(tz: str | None = None) -> str:
    """Return the current timezone-aware timestamp as an ISO formatted string."""

    zone_name = tz or os.getenv("SYDNEY_PULSE_TIMEZONE", DEFAULT_TIMEZONE)
    return datetime.now(tz=ZoneInfo(zone_name)).isoformat()


def sha256sum(path: Path | str) -> str:
    """Compute the SHA256 checksum for ``path``."""

    file_path = Path(path)
    hasher = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_dataframe(df: DataFrame, path: Path | str, *, index: bool = False) -> Path:
    """Persist a :class:`pandas.DataFrame` to ``path`` ensuring directories exist."""

    file_path = Path(path)
    ensure_directory(file_path)
    df.to_csv(file_path, index=index)
    return file_path


def _resolve_registry_path(path: Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    override = os.getenv(DATASET_REGISTRY_ENV)
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[1] / "DATASET_REGISTRY.yaml"


def update_registry(
    dataset_name: str,
    metadata: Mapping[str, object],
    *,
    registry_path: Path | None = None,
) -> Path:
    """Append or update metadata for ``dataset_name`` in the dataset registry."""

    path = _resolve_registry_path(registry_path)
    ensure_directory(path)
    records: dict[str, dict[str, object]]
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            records = yaml.safe_load(handle) or {}
    else:
        records = {}
    records[str(dataset_name)] = dict(metadata)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(records, handle, sort_keys=True)
    return path


def write_csv(
    path: Path,
    rows: Iterable[Mapping[str, object]] | Iterable[Sequence[object]],
    fieldnames: Sequence[str] | None = None,
    *,
    include_header: bool = True,
    mode: str = "w",
) -> Path:
    """Write rows to ``path`` using the csv module."""

    ensure_directory(path)
    with path.open(mode=mode, newline="", encoding="utf-8") as csvfile:
        if fieldnames is None:
            writer = csv.writer(csvfile)
            for row in rows:
                writer.writerow(list(row))
        else:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if include_header and ("w" in mode or "x" in mode):
                writer.writeheader()
            for row in rows:
                if not isinstance(row, MutableMapping):
                    raise TypeError("Row must be a mapping when fieldnames are provided")
                writer.writerow(row)
    return path


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file into a list of dictionaries."""

    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        return [dict(row) for row in reader]


def write_dataframe(df: "pd.DataFrame", path: Path, *, index: bool = False, **kwargs: object) -> Path:
    """Persist a pandas :class:`DataFrame` to ``path`` as CSV."""

    ensure_directory(path)
    df.to_csv(path, index=index, **kwargs)
    return path


def local_now(tz: str) -> datetime:
    """Return the current time in the specified timezone."""

    return datetime.now(tz=ZoneInfo(tz))


def combine_date_time(date: datetime, local_time: time, tz: str) -> datetime:
    """Combine a naive date and a time into an aware datetime in ``tz``."""

    zone = ZoneInfo(tz)
    naive = datetime.combine(date.date(), local_time)
    return naive.replace(tzinfo=zone)


__all__ = [
    "ensure_directory",
    "write_csv",
    "read_csv",
    "write_dataframe",
    "local_now",
    "combine_date_time",
    "current_timestamp",
    "sha256sum",
    "write_dataframe",
    "update_registry",
]
