"""
Data service — loads and caches the CSV dataset.

All other services consume the DataFrame returned by get_dataframe().
The data is loaded once at startup and held in memory to avoid repeated
disk reads on every request.
"""

import pandas as pd
from functools import lru_cache
from pathlib import Path

from app.config import settings


@lru_cache(maxsize=1)
def get_dataframe() -> pd.DataFrame:
    """
    Load the energy demand CSV from disk and return a clean DataFrame.
    Results are cached after the first call (lru_cache with maxsize=1).
    """
    path = Path(settings.data_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}. "
            "Run `python data/generate_data.py` to create it."
        )

    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["demand_mw"] = pd.to_numeric(df["demand_mw"], errors="coerce")
    df = df.dropna(subset=["demand_mw", "timestamp"])
    return df


def get_recent_window(hours: int = 168) -> pd.DataFrame:
    """Return the most recent N hours of data (default: 7 days)."""
    df = get_dataframe()
    cutoff = df["timestamp"].max() - pd.Timedelta(hours=hours)
    return df[df["timestamp"] >= cutoff].copy()


def get_date_range(start: str | None, end: str | None) -> pd.DataFrame:
    """Filter the full dataset to an optional date range."""
    df = get_dataframe()
    if start:
        df = df[df["timestamp"] >= pd.Timestamp(start)]
    if end:
        df = df[df["timestamp"] <= pd.Timestamp(end)]
    return df
