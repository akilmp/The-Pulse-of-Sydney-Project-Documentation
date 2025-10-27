"""Streamlit entrypoint for the Sydney Pulse dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd
import streamlit as st

from src.viz.maps import build_schi_map
from src.viz.scatterplots import delay_vs_mood_scatter
from src.viz.timeseries import schi_timeseries_chart

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


DATASETS: Dict[str, dict[str, object]] = {
    "schi": {"filename": "schi.csv", "parse_dates": ["date"]},
    "commute": {"filename": "commute_features.csv", "parse_dates": ["date"]},
    "weather": {"filename": "weather_features.csv", "parse_dates": ["date"]},
}


@st.cache_data(show_spinner=False)
def load_dataset(name: str) -> pd.DataFrame:
    """Load a processed dataset from ``data/processed``.

    The function is cached to avoid repeated disk reads during interaction.
    """

    config = DATASETS[name]
    path = PROCESSED_DIR / str(config["filename"])
    parse_dates = config.get("parse_dates")

    if not path.exists():
        raise FileNotFoundError(
            f"Expected processed dataset '{path.name}' under '{PROCESSED_DIR}'."
        )

    return pd.read_csv(path, parse_dates=parse_dates)


def _normalise_weights(raw_weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(raw_weights.values())
    if total <= 0:
        count = len(raw_weights) or 1
        return {key: 1.0 / count for key in raw_weights}
    return {key: value / total for key, value in raw_weights.items()}


def _render_weight_controls() -> Dict[str, float]:
    st.sidebar.subheader("SCHI weights")
    st.sidebar.caption(
        "Adjust the contribution of each component. We normalise the sliders so "
        "the weights always sum to 100%."
    )

    reliability = st.sidebar.slider(
        "Reliability (Delays)",
        min_value=0,
        max_value=100,
        value=35,
        step=5,
        help="Higher weight emphasises low average delay and consistent journeys.",
    )
    mood = st.sidebar.slider(
        "Mood",
        min_value=0,
        max_value=100,
        value=25,
        step=5,
        help="Personal and public sentiment about the commute experience.",
    )
    rain = st.sidebar.slider(
        "Rain Comfort",
        min_value=0,
        max_value=100,
        value=20,
        step=5,
        help="Penalises heavy rainfall days that make commuting harder.",
    )
    temperature = st.sidebar.slider(
        "Temperature Stability",
        min_value=0,
        max_value=100,
        value=20,
        step=5,
        help="Rewards days with smaller temperature swings between morning and evening.",
    )

    weights = _normalise_weights(
        {
            "reliability": float(reliability),
            "mood": float(mood),
            "rain_comfort": float(rain),
            "temperature": float(temperature),
        }
    )
    st.sidebar.caption(
        "Final weights: "
        + ", ".join(f"{key.title()}: {value * 100:.1f}%" for key, value in weights.items())
    )
    return weights


def _recompute_schi(df: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
    required = {
        "reliability_score",
        "mood_score",
        "rain_comfort_score",
        "temperature_score",
    }
    for column in required.union({"schi", "trip_count"}):
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    if required.issubset(df.columns):
        recomputed = (
            df["reliability_score"].astype(float) * weights["reliability"]
            + df["mood_score"].astype(float) * weights["mood"]
            + df["rain_comfort_score"].astype(float) * weights["rain_comfort"]
            + df["temperature_score"].astype(float) * weights["temperature"]
        )
        df = df.copy()
        df["schi_weighted"] = recomputed * 100
    else:
        df = df.copy()
        if "schi" in df.columns:
            df["schi_weighted"] = df["schi"].astype(float)
        else:
            df["schi_weighted"] = float("nan")
    return df


def _kpi_metric(label: str, value: float | str, delta: float | None = None) -> None:
    formatted_value = value
    formatted_delta = None if delta is None else f"{delta:+.1f}"
    if isinstance(value, (int, float)):
        formatted_value = f"{value:.1f}"
    st.metric(label, formatted_value, formatted_delta)


def _render_overview(schi_df: pd.DataFrame) -> None:
    st.header("Overview")
    if schi_df.empty:
        st.info("Processed SCHI dataset is empty. Run the data pipeline to populate it.")
        return

    latest = schi_df.sort_values("date").dropna(subset=["schi_weighted"])
    if latest.empty:
        st.warning("SCHI values are missing for the loaded dataset.")
        return

    current_day = latest.iloc[-1]
    average = latest["schi_weighted"].mean()
    grouped = latest.groupby("sa2_code", dropna=False)["schi_weighted"].mean().dropna()
    if grouped.empty:
        st.warning("SCHI values are missing for the loaded dataset.")
        return
    best = grouped.idxmax()
    worst = grouped.idxmin()
    best_value = grouped.loc[best]
    worst_value = grouped.loc[worst]

    code_to_label = {
        row.get("sa2_code"): row.get("sa2_name", row.get("sa2_code"))
        for _, row in latest.iterrows()
    }

    col1, col2, col3 = st.columns(3)
    with col1:
        _kpi_metric("Sydney average SCHI", average)
    with col2:
        _kpi_metric("Latest reading", current_day["schi_weighted"])
    with col3:
        observations = (
            float(latest["trip_count"].sum()) if "trip_count" in latest else float(len(latest))
        )
        _kpi_metric("Observations", observations)

    col4, col5 = st.columns(2)
    with col4:
        _kpi_metric("Top performer", f"{code_to_label.get(best, best)} ({best_value:.1f})")
    with col5:
        _kpi_metric("Needs attention", f"{code_to_label.get(worst, worst)} ({worst_value:.1f})")

    st.subheader("Daily trend")
    daily = latest.groupby("date", as_index=False)["schi_weighted"].mean()
    daily["series"] = "Sydney average"
    chart = schi_timeseries_chart(
        daily,
        value_col="schi_weighted",
        group_col="series",
        title="SCHI trend across all SA2 areas",
    )
    st.altair_chart(chart, use_container_width=True)

    st.download_button(
        "Download SCHI (CSV)",
        data=latest.to_csv(index=False).encode("utf-8"),
        file_name="schi_latest.csv",
        mime="text/csv",
    )


def _render_map(schi_df: pd.DataFrame) -> None:
    st.header("Map")
    if schi_df.empty:
        st.info("No SCHI data available to plot on the map.")
        return

    map_chart, metadata = build_schi_map(
        schi_df,
        value_col="schi_weighted",
        tooltip_fields=["sa2_code", "sa2_name", "schi_weighted", "reliability_score"],
    )
    if metadata.get("warning"):
        st.warning(metadata["warning"])
    st.altair_chart(map_chart, use_container_width=True)

    st.download_button(
        "Download SA2 snapshot",
        data=schi_df.to_csv(index=False).encode("utf-8"),
        file_name="schi_map_snapshot.csv",
        mime="text/csv",
    )


def _render_compare(schi_df: pd.DataFrame, commute_df: pd.DataFrame) -> None:
    st.header("Compare suburbs")
    if schi_df.empty:
        st.info("Load SCHI features to enable comparisons.")
        return

    available_codes = sorted(set(schi_df["sa2_code"].astype(str)))
    default_selection = available_codes[:3]
    selected_codes = st.multiselect(
        "Select SA2 areas",
        options=available_codes,
        default=default_selection,
        help="Choose up to ten areas to compare their SCHI time series.",
    )
    filtered = schi_df if not selected_codes else schi_df[schi_df["sa2_code"].isin(selected_codes)]
    label_column = "sa2_name" if "sa2_name" in filtered.columns else "sa2_code"
    chart = schi_timeseries_chart(
        filtered,
        value_col="schi_weighted",
        group_col=label_column,
        title="SCHI comparison",
    )
    st.altair_chart(chart, use_container_width=True)

    if not commute_df.empty:
        merged = pd.merge(
            filtered,
            commute_df,
            on=["sa2_code", "date"],
            how="left",
            suffixes=("", "_commute"),
        )
        scatter = delay_vs_mood_scatter(
            merged.dropna(subset=["avg_delay_min", "avg_mood"]),
            x="avg_delay_min",
            y="avg_mood",
            color_col=label_column,
            size_col="trip_count",
        )
        st.altair_chart(scatter, use_container_width=True)

    st.download_button(
        "Download selection",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="schi_compare_selection.csv",
        mime="text/csv",
    )


def _render_my_commute(commute_df: pd.DataFrame) -> None:
    st.header("My Commute")
    if commute_df.empty:
        st.info("Personal commute features are missing. Upload logs and run the pipeline.")
        return

    st.markdown(
        "Use this view to dig into the self-logged commute dataset. The scatter plot "
        "highlights the trade-off between delays and mood across the selected period."
    )

    available_dates = sorted(commute_df["date"].unique())
    if available_dates:
        start_date, end_date = st.select_slider(
            "Select date range",
            options=available_dates,
            value=(available_dates[0], available_dates[-1]),
            help="Filter the commute log to a specific time window.",
        )
        commute_df = commute_df[(commute_df["date"] >= start_date) & (commute_df["date"] <= end_date)]

    summary = commute_df.agg({"avg_delay_min": "mean", "avg_mood": "mean", "trip_count": "sum"})
    col1, col2, col3 = st.columns(3)
    _kpi_metric("Average delay (min)", float(summary.get("avg_delay_min", 0.0)))
    _kpi_metric("Average mood", float(summary.get("avg_mood", 0.0)))
    _kpi_metric("Trips analysed", float(summary.get("trip_count", 0.0)))

    commute_chart = schi_timeseries_chart(
        commute_df,
        value_col="avg_delay_min",
        group_col="sa2_code",
        title="Average delay by date",
    )
    st.altair_chart(commute_chart, use_container_width=True)

    scatter = delay_vs_mood_scatter(
        commute_df,
        x="avg_delay_min",
        y="avg_mood",
        color_col="sa2_code",
        size_col="trip_count",
    )
    st.altair_chart(scatter, use_container_width=True)

    st.download_button(
        "Download commute features",
        data=commute_df.to_csv(index=False).encode("utf-8"),
        file_name="commute_features_filtered.csv",
        mime="text/csv",
    )


def _prepare_datasets() -> Dict[str, pd.DataFrame]:
    loaded: Dict[str, pd.DataFrame] = {}
    for name in DATASETS:
        try:
            loaded[name] = load_dataset(name)
        except FileNotFoundError as exc:
            st.sidebar.warning(str(exc))
            loaded[name] = pd.DataFrame()
    return loaded


def _ensure_processed_directory() -> None:
    if not PROCESSED_DIR.exists():
        st.error(
            "Processed directory missing. Run the data pipeline (e.g. `make features`) "
            "to populate 'data/processed/'."
        )
        st.stop()


def main() -> None:
    """Render the interactive Sydney Pulse dashboard."""

    st.set_page_config(page_title="Sydney Pulse Dashboard", page_icon="🌀", layout="wide")
    st.title("Sydney Pulse Dashboard")

    _ensure_processed_directory()
    weights = _render_weight_controls()
    datasets = _prepare_datasets()

    schi_df = _recompute_schi(datasets.get("schi", pd.DataFrame()), weights)
    commute_df = datasets.get("commute", pd.DataFrame())

    pages = {
        "Overview": lambda: _render_overview(schi_df),
        "Map": lambda: _render_map(schi_df),
        "Compare": lambda: _render_compare(schi_df, commute_df),
        "My Commute": lambda: _render_my_commute(commute_df),
    }

    st.sidebar.subheader("Pages")
    choice = st.sidebar.radio(
        "Navigate", list(pages), help="Jump between dashboard perspectives."
    )
    pages[choice]()


if __name__ == "__main__":
    main()
