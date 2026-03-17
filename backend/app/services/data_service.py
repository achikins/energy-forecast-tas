"""
Data service — fetches live TAS1 demand data from AEMO and caches it in memory.

Strategy:
  - On startup, fetch the last 7 days of live 5-minute dispatch data from AEMO.
  - Cache the result in-process; refresh every CACHE_TTL_SECONDS in the background.
  - If AEMO is unreachable, fall back to the bundled CSV so the app stays up.
"""

import io
import logging
import urllib.request
import zipfile
from datetime import date, timedelta, datetime, timezone
from pathlib import Path
from threading import Lock

import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

# How many days of history to keep in memory (7 days = ~2,016 5-min rows → ~336 hourly)
HISTORY_DAYS = 30

# Re-fetch from AEMO every N seconds (1 hour)
CACHE_TTL_SECONDS = 3600

# AEMO monthly archive URL template (used for older months)
ARCHIVE_URL = (
    "https://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/"
    "{year}/MMSDM_{year}_{month:02d}/MMSDM_Historical_Data_SQLLoader/DATA/"
    "PUBLIC_ARCHIVE%23DISPATCHREGIONSUM%23FILE01%23{year}{month:02d}010000.zip"
)

# AEMO current-day dispatch file (updates every 5 minutes)
CURRENT_URL = "https://nemweb.com.au/Reports/Current/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_{dt}.zip"

# ── In-memory cache ────────────────────────────────────────────────────────────

_cache_lock = Lock()
_cached_df: pd.DataFrame | None = None
_cached_at: datetime | None = None


# ── AEMO fetch helpers ─────────────────────────────────────────────────────────

def _fetch_zip_csv(url: str, timeout: int = 30) -> bytes | None:
    """Download a ZIP from AEMO and return the first CSV file's bytes."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            raw = resp.read()
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            return zf.read(zf.namelist()[0])
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None


def _parse_dispatchregionsum(csv_bytes: bytes) -> pd.DataFrame:
    """Parse AEMO DISPATCHREGIONSUM CSV bytes into a clean TAS1 DataFrame."""
    lines = csv_bytes.decode("utf-8", errors="replace").splitlines()
    data_lines = [l for l in lines if l.startswith("D,DISPATCH,REGIONSUM")]
    if not data_lines:
        return pd.DataFrame()

    header_lines = [l for l in lines if l.startswith("I,DISPATCH,REGIONSUM")]
    cols = header_lines[0].split(",") if header_lines else None

    df = pd.read_csv(io.StringIO("\n".join(data_lines)), header=None, names=cols)
    df.columns = [str(c).strip().upper() for c in df.columns]

    df = df[(df["REGIONID"] == "TAS1") & (df["INTERVENTION"] == 0)].copy()
    if df.empty:
        return pd.DataFrame()

    df["timestamp"] = pd.to_datetime(df["SETTLEMENTDATE"], format="%Y/%m/%d %H:%M:%S")
    df["demand_mw"] = pd.to_numeric(df["TOTALDEMAND"], errors="coerce")
    df["region"] = "TAS"
    return df[["timestamp", "demand_mw", "region"]].dropna()


def _fetch_live() -> pd.DataFrame | None:
    """
    Fetch the last HISTORY_DAYS of TAS1 demand from AEMO monthly archives.
    Returns hourly-resampled DataFrame or None on total failure.
    """
    today = date.today()
    # Collect the unique (year, month) pairs we need
    months_needed: set[tuple[int, int]] = set()
    for d in range(HISTORY_DAYS + 1):
        day = today - timedelta(days=d)
        months_needed.add((day.year, day.month))

    frames = []
    for year, month in sorted(months_needed):
        url = ARCHIVE_URL.format(year=year, month=month)
        logger.info("Fetching AEMO archive %d-%02d ...", year, month)
        csv_bytes = _fetch_zip_csv(url, timeout=60)
        if csv_bytes:
            df = _parse_dispatchregionsum(csv_bytes)
            if not df.empty:
                frames.append(df)

    if not frames:
        return None

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("timestamp").drop_duplicates("timestamp")

    # Keep only the last HISTORY_DAYS
    cutoff = pd.Timestamp(today - timedelta(days=HISTORY_DAYS))
    combined = combined[combined["timestamp"] >= cutoff]

    # Resample to hourly
    combined = combined.set_index("timestamp")
    hourly = combined["demand_mw"].resample("h").mean().round(2).reset_index()
    hourly["region"] = "TAS"
    return hourly


def _load_csv_fallback() -> pd.DataFrame:
    """Load the bundled CSV as a fallback when AEMO is unreachable."""
    path = Path(settings.data_path)
    if not path.exists():
        raise FileNotFoundError(
            f"No fallback CSV at {path} and AEMO fetch failed. "
            "Run `python data/fetch_aemo_data.py` to generate it."
        )
    logger.warning("Using CSV fallback: %s", path)
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["demand_mw"] = pd.to_numeric(df["demand_mw"], errors="coerce")
    return df.dropna(subset=["demand_mw", "timestamp"])


# ── Public API ─────────────────────────────────────────────────────────────────

def refresh_data() -> None:
    """
    Fetch fresh data from AEMO and update the in-memory cache.
    Falls back to CSV if AEMO is unreachable. Safe to call from a background thread.
    """
    global _cached_df, _cached_at
    logger.info("Refreshing AEMO data...")
    df = _fetch_live()
    if df is None or df.empty:
        logger.warning("AEMO fetch returned no data — falling back to CSV.")
        try:
            df = _load_csv_fallback()
        except FileNotFoundError as e:
            logger.error("Fallback CSV also unavailable: %s", e)
            return

    with _cache_lock:
        _cached_df = df
        _cached_at = datetime.now(timezone.utc)

    logger.info(
        "Data cache updated: %d hourly rows, %s → %s",
        len(df),
        df["timestamp"].min(),
        df["timestamp"].max(),
    )


def get_dataframe() -> pd.DataFrame:
    """Return the cached DataFrame, refreshing if the cache is empty."""
    with _cache_lock:
        df = _cached_df

    if df is None:
        # First call before background task has run — block and fetch now
        refresh_data()
        with _cache_lock:
            df = _cached_df

    if df is None:
        raise RuntimeError("No data available — AEMO unreachable and no fallback CSV.")

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


def cache_age_seconds() -> float | None:
    """Return how many seconds ago the cache was last updated, or None if never."""
    with _cache_lock:
        if _cached_at is None:
            return None
    return (datetime.now(timezone.utc) - _cached_at).total_seconds()
