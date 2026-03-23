"""
Energy Decision Layer service.

Derives two signals from the 48-hour demand forecast:
  1. Best times to use energy  — windows where forecast demand is lowest
     (i.e. grid is least stressed, prices tend to be lower).
  2. Expected peak generation hours — windows where forecast demand is
     highest (generation must ramp up to meet load; hydro / wind running
     at or near capacity).

All logic is deterministic and rule-based, built on top of the existing
Holt-Winters forecast so no additional data sources are needed.
"""

from datetime import datetime, timezone

import pandas as pd

from app.models.decision import BestUsageWindow, DecisionSummary, PeakGenerationWindow
from app.services.forecast_service import generate_forecast

# Number of best-use and peak-generation windows to surface
_NUM_BEST = 3
_NUM_PEAK = 3

# Minimum window length in hours (avoid 1-hour slivers)
_MIN_WINDOW_H = 2


def compute_decision() -> DecisionSummary:
    """
    Generate the Energy Decision Layer from the next 48-hour forecast.
    """
    forecast = generate_forecast(periods=48)
    points = forecast.data

    if not points:
        raise ValueError("Forecast returned no data.")

    # Build a DataFrame for easy manipulation
    df = pd.DataFrame(
        [
            {
                "timestamp": pd.Timestamp(p.timestamp),
                "predicted_mw": p.predicted_mw,
            }
            for p in points
        ]
    )

    avg_mw = df["predicted_mw"].mean()
    std_mw = df["predicted_mw"].std()

    # ── Best usage windows (lowest demand, consecutive blocks) ──────────
    low_threshold = avg_mw - 0.25 * std_mw
    best_windows = _extract_windows(
        df,
        condition=df["predicted_mw"] <= low_threshold,
        top_n=_NUM_BEST,
        ascending=True,   # sort by avg demand asc (lowest first)
    )

    best_usage = []
    for w in best_windows:
        duration = w["end_hour"] - w["start_hour"]
        reason = (
            f"Demand forecast is ~{w['avg_mw']:.0f} MW over this window — "
            f"{abs(w['avg_mw'] - avg_mw):.0f} MW below the 48-hour average. "
            f"Grid stress is low; ideal for high-consumption tasks."
        )
        best_usage.append(
            BestUsageWindow(
                start_hour=w["start_hour"],
                end_hour=w["end_hour"],
                label=_hour_label(w["start_ts"], w["end_ts"]),
                avg_demand_mw=round(w["avg_mw"], 1),
                reason=reason,
            )
        )

    # ── Peak generation windows (highest demand, consecutive blocks) ────
    high_threshold = avg_mw + 0.25 * std_mw
    peak_windows = _extract_windows(
        df,
        condition=df["predicted_mw"] >= high_threshold,
        top_n=_NUM_PEAK,
        ascending=False,  # sort by avg demand desc (highest first)
    )

    peak_gen = []
    for w in peak_windows:
        excess = w["avg_mw"] - avg_mw
        confidence = "high" if excess > std_mw else ("medium" if excess > 0.5 * std_mw else "low")
        note = (
            f"Demand expected to peak around {w['avg_mw']:.0f} MW. "
            f"Hydro and wind generation will likely be running near capacity."
        )
        peak_gen.append(
            PeakGenerationWindow(
                start_hour=w["start_hour"],
                end_hour=w["end_hour"],
                label=_hour_label(w["start_ts"], w["end_ts"]),
                expected_demand_mw=round(w["avg_mw"], 1),
                confidence=confidence,
                note=note,
            )
        )

    # ── Top-level advice ────────────────────────────────────────────────
    if best_usage:
        advice = (
            f"Best time to use energy in the next 48 hours: {best_usage[0].label}. "
            f"Avoid {peak_gen[0].label} if possible — peak grid load expected."
            if peak_gen
            else f"Lowest grid load forecast: {best_usage[0].label}."
        )
    else:
        advice = "Demand is relatively flat over the next 48 hours — no strong preference."

    return DecisionSummary(
        best_usage_windows=best_usage,
        peak_generation_windows=peak_gen,
        advice=advice,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )


# ── Helpers ──────────────────────────────────────────────────────────────────

def _extract_windows(
    df: pd.DataFrame,
    condition: pd.Series,
    top_n: int,
    ascending: bool,
) -> list[dict]:
    """
    Find contiguous blocks of rows where `condition` is True,
    then return the top_n blocks sorted by their average predicted_mw.
    Blocks shorter than _MIN_WINDOW_H are filtered out.
    If no blocks meet the threshold, fall back to the full top_n single-hour
    extremes so we always return something useful.
    """
    df = df.copy()
    df["flag"] = condition.values
    df["group"] = (df["flag"] != df["flag"].shift()).cumsum()

    blocks = []
    for _gid, grp in df.groupby("group"):
        if not grp["flag"].iloc[0]:
            continue
        if len(grp) < _MIN_WINDOW_H:
            continue
        blocks.append(
            {
                "start_ts": grp["timestamp"].iloc[0],
                "end_ts": grp["timestamp"].iloc[-1],
                "start_hour": grp["timestamp"].iloc[0].hour,
                "end_hour": grp["timestamp"].iloc[-1].hour,
                "avg_mw": grp["predicted_mw"].mean(),
            }
        )

    # Fallback: if threshold produced no long-enough blocks, use individual
    # hours as single-entry windows
    if not blocks:
        sorted_df = df.sort_values("predicted_mw", ascending=ascending).head(top_n)
        for _, row in sorted_df.iterrows():
            blocks.append(
                {
                    "start_ts": row["timestamp"],
                    "end_ts": row["timestamp"],
                    "start_hour": row["timestamp"].hour,
                    "end_hour": row["timestamp"].hour,
                    "avg_mw": row["predicted_mw"],
                }
            )

    blocks.sort(key=lambda b: b["avg_mw"], reverse=not ascending)
    return blocks[:top_n]


def _hour_label(start: pd.Timestamp, end: pd.Timestamp) -> str:
    """Format a window as 'Mon 02:00 – 06:00' or 'Mon 02:00 – Tue 06:00'."""
    start_str = start.strftime("%a %H:%M")
    if start.date() == end.date():
        end_str = (end + pd.Timedelta(hours=1)).strftime("%H:%M")
    else:
        end_str = (end + pd.Timedelta(hours=1)).strftime("%a %H:%M")
    return f"{start_str} – {end_str}"
