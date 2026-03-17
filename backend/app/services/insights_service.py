"""
Insights service — derives analytical summaries from historical demand data.

Detects anomalies using a rolling z-score approach, identifies peak periods,
calculates trend direction, and generates a human-readable narrative summary.
All logic is rule-based and deterministic — no ML required.
"""

import pandas as pd
import numpy as np

from app.models.insights import AnomalyRecord, InsightsSummary, PeakPeriod
from app.services.data_service import get_dataframe

# A demand reading is flagged as anomalous when its z-score exceeds this threshold
_ANOMALY_Z_THRESHOLD = 2.5

# Rolling window for z-score calculation (hours)
_ROLLING_WINDOW = 24

# Number of top peak periods to return
_TOP_PEAKS = 5


def compute_insights(hours: int = 168) -> InsightsSummary:
    """
    Compute insights over the most recent `hours` of data (default: 7 days).
    """
    df = get_dataframe()
    cutoff = df["timestamp"].max() - pd.Timedelta(hours=hours)
    window_df = df[df["timestamp"] >= cutoff].copy()

    if window_df.empty:
        raise ValueError("No data available in the requested window.")

    demand = window_df["demand_mw"]

    # --- Basic statistics ---
    avg_demand = round(demand.mean(), 2)
    peak_idx = demand.idxmax()
    min_idx = demand.idxmin()
    peak_mw = round(demand.max(), 2)
    min_mw = round(demand.min(), 2)
    peak_ts = window_df.loc[peak_idx, "timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    min_ts = window_df.loc[min_idx, "timestamp"].strftime("%Y-%m-%d %H:%M:%S")

    # --- Trend: compare first half vs second half of the window ---
    mid = len(window_df) // 2
    first_half_avg = window_df.iloc[:mid]["demand_mw"].mean()
    second_half_avg = window_df.iloc[mid:]["demand_mw"].mean()
    trend_change_pct = round((second_half_avg - first_half_avg) / first_half_avg * 100, 2)

    if trend_change_pct > 3:
        trend = "rising"
    elif trend_change_pct < -3:
        trend = "falling"
    else:
        trend = "stable"

    # --- Anomaly detection via rolling z-score ---
    rolling_mean = demand.rolling(window=_ROLLING_WINDOW, min_periods=1).mean()
    rolling_std = demand.rolling(window=_ROLLING_WINDOW, min_periods=1).std().fillna(1)
    z_scores = (demand - rolling_mean) / rolling_std

    anomaly_mask = z_scores.abs() > _ANOMALY_Z_THRESHOLD
    anomaly_rows = window_df[anomaly_mask].head(10)  # cap at 10 anomalies

    anomalies = [
        AnomalyRecord(
            timestamp=row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            demand_mw=round(row["demand_mw"], 2),
            deviation_pct=round(abs(z_scores[idx]) / _ANOMALY_Z_THRESHOLD * 100, 1),
            description=_describe_anomaly(row["demand_mw"], avg_demand),
        )
        for idx, row in anomaly_rows.iterrows()
    ]

    # --- Top peak periods ---
    top_peaks_df = window_df.nlargest(_TOP_PEAKS, "demand_mw")
    top_peaks = [
        PeakPeriod(
            timestamp=row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            demand_mw=round(row["demand_mw"], 2),
            hour_of_day=row["timestamp"].hour,
            day_of_week=row["timestamp"].strftime("%A"),
        )
        for _, row in top_peaks_df.iterrows()
    ]

    # --- Narrative summary ---
    summary = _build_summary(avg_demand, peak_mw, peak_ts, trend, trend_change_pct, len(anomalies))

    return InsightsSummary(
        average_demand_mw=avg_demand,
        peak_demand_mw=peak_mw,
        peak_timestamp=peak_ts,
        min_demand_mw=min_mw,
        min_timestamp=min_ts,
        demand_trend=trend,
        trend_change_pct=trend_change_pct,
        anomalies=anomalies,
        top_peak_periods=top_peaks,
        summary_text=summary,
    )


def _describe_anomaly(demand_mw: float, avg_mw: float) -> str:
    """Return a short plain-text label for an anomalous reading."""
    if demand_mw > avg_mw:
        pct = round((demand_mw - avg_mw) / avg_mw * 100, 1)
        return f"Demand spike: {pct}% above rolling average"
    else:
        pct = round((avg_mw - demand_mw) / avg_mw * 100, 1)
        return f"Demand drop: {pct}% below rolling average"


def _build_summary(
    avg: float,
    peak: float,
    peak_ts: str,
    trend: str,
    change_pct: float,
    anomaly_count: int,
) -> str:
    """Compose a human-readable narrative from key metrics."""
    direction = "increased" if change_pct > 0 else "decreased"
    trend_sentence = (
        f"Demand has {direction} by {abs(change_pct):.1f}% over the analysis window."
        if trend != "stable"
        else "Demand has remained relatively stable over the analysis window."
    )
    anomaly_sentence = (
        f"{anomaly_count} anomalous readings were detected."
        if anomaly_count > 0
        else "No significant anomalies were detected."
    )
    return (
        f"Average demand is {avg:.0f} MW. "
        f"Peak demand of {peak:.0f} MW occurred at {peak_ts}. "
        f"{trend_sentence} {anomaly_sentence}"
    )
