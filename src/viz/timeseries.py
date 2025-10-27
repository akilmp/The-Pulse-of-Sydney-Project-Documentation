"""Time series visualisations used across the project."""

from __future__ import annotations

from typing import Optional

import altair as alt
import pandas as pd


def _fallback_chart(message: str) -> alt.Chart:
    return (
        alt.Chart(pd.DataFrame({"text": [message]}))
        .mark_text(size=16)
        .encode(text="text")
        .properties(height=320)
    )


def schi_timeseries_chart(
    df: pd.DataFrame,
    *,
    value_col: str,
    group_col: Optional[str] = None,
    title: Optional[str] = None,
) -> alt.Chart:
    """Build a simple line chart for SCHI (or related metrics) over time."""

    if df.empty or value_col not in df.columns or "date" not in df.columns:
        return _fallback_chart("No time series data")

    data = df.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data[value_col] = pd.to_numeric(data[value_col], errors="coerce")
    data = data.dropna(subset=["date", value_col])
    if data.empty:
        return _fallback_chart("No time series data")

    line = alt.Chart(data).mark_line(point=True).encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y(f"{value_col}:Q", title=value_col.replace("_", " ").title()),
    )

    tooltip = [alt.Tooltip("date:T", title="Date"), alt.Tooltip(value_col, title="Value", format=".2f")]

    if group_col and group_col in data.columns:
        line = line.encode(color=alt.Color(f"{group_col}:N", title=group_col.replace("_", " ").title()))
        tooltip.insert(1, alt.Tooltip(group_col, title=group_col.replace("_", " ").title()))
    else:
        line = line.encode(color=alt.value("#0052A3"))

    chart = line.encode(tooltip=tooltip).properties(height=360)
    if title:
        chart = chart.properties(title=title)
    return chart
