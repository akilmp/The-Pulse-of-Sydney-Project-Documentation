"""Scatter plot helpers shared by dashboards and notebooks."""

from __future__ import annotations

from typing import Optional

import altair as alt
import pandas as pd


def delay_vs_mood_scatter(
    df: pd.DataFrame,
    *,
    x: str,
    y: str,
    color_col: Optional[str] = None,
    size_col: Optional[str] = None,
    title: Optional[str] = None,
) -> alt.Chart:
    """Build a scatter plot comparing average delays and mood scores."""

    if df.empty or x not in df.columns or y not in df.columns:
        return (
            alt.Chart(pd.DataFrame({"text": ["No scatter data"]}))
            .mark_text(size=16)
            .encode(text="text")
            .properties(height=320)
        )

    data = df.copy()
    data[x] = pd.to_numeric(data[x], errors="coerce")
    data[y] = pd.to_numeric(data[y], errors="coerce")
    if size_col and size_col in data.columns:
        data[size_col] = pd.to_numeric(data[size_col], errors="coerce")
    data = data.dropna(subset=[x, y])
    if data.empty:
        return (
            alt.Chart(pd.DataFrame({"text": ["No scatter data"]}))
            .mark_text(size=16)
            .encode(text="text")
            .properties(height=320)
        )

    mark = alt.Chart(data).mark_circle(opacity=0.7)
    encoding = {
        "x": alt.X(f"{x}:Q", title=x.replace("_", " ").title()),
        "y": alt.Y(f"{y}:Q", title=y.replace("_", " ").title()),
        "tooltip": [
            alt.Tooltip(x, title=x.replace("_", " ").title(), format=".2f"),
            alt.Tooltip(y, title=y.replace("_", " ").title(), format=".2f"),
        ],
    }

    if color_col and color_col in data.columns:
        encoding["color"] = alt.Color(
            f"{color_col}:N", title=color_col.replace("_", " ").title()
        )
        encoding["tooltip"].append(
            alt.Tooltip(color_col, title=color_col.replace("_", " ").title())
        )
    else:
        encoding["color"] = alt.value("#F26419")

    if size_col and size_col in data.columns:
        encoding["size"] = alt.Size(
            f"{size_col}:Q",
            title=size_col.replace("_", " ").title(),
            scale=alt.Scale(range=[40, 400]),
        )
        encoding["tooltip"].append(
            alt.Tooltip(size_col, title=size_col.replace("_", " ").title(), format=".0f")
        )

    chart = mark.encode(**encoding).properties(height=360)
    if title:
        chart = chart.properties(title=title)
    return chart
