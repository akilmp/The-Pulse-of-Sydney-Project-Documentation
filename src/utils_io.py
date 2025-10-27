"""I/O utilities shared across the Sydney Pulse project."""

from __future__ import annotations

import csv
from datetime import datetime, time
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Sequence, TYPE_CHECKING

from zoneinfo import ZoneInfo


if TYPE_CHECKING:  # pragma: no cover - type checking only
    import pandas as pd


def ensure_directory(path: Path) -> Path:
    """Ensure that the directory for ``path`` exists and return it."""

    directory = path if path.is_dir() else path.parent
    directory.mkdir(parents=True, exist_ok=True)
    return directory


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
]
