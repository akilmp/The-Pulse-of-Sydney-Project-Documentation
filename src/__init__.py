"""Top-level package for the Sydney Pulse project."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:  # pragma: no cover - best effort
    __version__ = version("sydney-pulse")
except PackageNotFoundError:  # pragma: no cover - fallback during local dev
    __version__ = "0.1.0"

__all__ = ["__version__"]
