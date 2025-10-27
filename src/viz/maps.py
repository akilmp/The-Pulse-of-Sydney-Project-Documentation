"""Mapping utilities shared between the Streamlit app and notebooks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import altair as alt
import pandas as pd

try:  # pragma: no cover - optional dependency at runtime
    from shapely import wkt
except ModuleNotFoundError:  # pragma: no cover - gracefully degrade when absent
    wkt = None


@dataclass
class MapMetadata:
    """Holds auxiliary information about the rendered map."""

    warning: str | None = None

    def as_dict(self) -> Dict[str, str]:
        return {"warning": self.warning} if self.warning else {}


def _compute_centroids(geometry_values: Iterable[str]) -> Tuple[List[float | None], List[float | None]]:
    longitudes: List[float | None] = []
    latitudes: List[float | None] = []
    for value in geometry_values:
        if not value:
            longitudes.append(None)
            latitudes.append(None)
            continue
        if wkt is None:
            longitudes.append(None)
            latitudes.append(None)
            continue
        try:
            geom = wkt.loads(value)
        except Exception:  # pragma: no cover - defensive against malformed WKT
            longitudes.append(None)
            latitudes.append(None)
            continue
        centroid = geom.centroid
        longitudes.append(float(centroid.x))
        latitudes.append(float(centroid.y))
    return longitudes, latitudes


def _prepare_map_data(df: pd.DataFrame, value_col: str) -> Tuple[pd.DataFrame, MapMetadata]:
    metadata = MapMetadata()
    if df.empty:
        return df, metadata

    data = df.copy()
    if {"longitude", "latitude"}.issubset(data.columns):
        data["longitude"] = pd.to_numeric(data["longitude"], errors="coerce")
        data["latitude"] = pd.to_numeric(data["latitude"], errors="coerce")
    elif "geometry_wkt" in data.columns:
        longitudes, latitudes = _compute_centroids(data["geometry_wkt"])
        data["longitude"] = longitudes
        data["latitude"] = latitudes
        if wkt is None:
            metadata.warning = (
                "Install 'shapely' to render precise polygons. Falling back to centroid markers."
            )
    else:
        metadata.warning = (
            "Dataset lacks geometry information. Add 'geometry_wkt' or latitude/longitude columns."
        )

    numeric = pd.to_numeric(data.get(value_col, pd.Series(dtype=float)), errors="coerce")
    data[value_col] = numeric
    data = data.dropna(subset=["longitude", "latitude", value_col])
    return data, metadata


def build_schi_map(
    df: pd.DataFrame,
    *,
    value_col: str = "schi_weighted",
    tooltip_fields: Iterable[str] | None = None,
) -> Tuple[alt.Chart, Dict[str, str]]:
    """Create a point-based map of SCHI scores using Altair."""

    prepared, metadata = _prepare_map_data(df, value_col)
    if prepared.empty:
        fallback = alt.Chart(pd.DataFrame({"text": ["No map data"]})).mark_text(
            size=16
        ).encode(text="text")
        return fallback.properties(height=360), metadata.as_dict()

    tooltip = []
    if tooltip_fields:
        for field in tooltip_fields:
            if field in prepared.columns:
                dtype = "Q" if pd.api.types.is_numeric_dtype(prepared[field]) else "N"
                tooltip.append(
                    alt.Tooltip(f"{field}:{dtype}", title=field.replace("_", " ").title())
                )
    tooltip.append(alt.Tooltip(f"{value_col}:Q", title="SCHI", format=".1f"))

    chart = (
        alt.Chart(prepared)
        .mark_circle(opacity=0.85)
        .encode(
            longitude="longitude:Q",
            latitude="latitude:Q",
            color=alt.Color(f"{value_col}:Q", title="SCHI", scale=alt.Scale(scheme="blues")),
            size=alt.Size(f"{value_col}:Q", title="SCHI", scale=alt.Scale(range=[100, 1200])),
            tooltip=tooltip,
        )
        .project(type="mercator")
        .properties(height=500, title="Sydney Commute Happiness Index (SCHI)")
    )
    return chart, metadata.as_dict()
