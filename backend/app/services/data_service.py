"""
Data service — fetches live TAS1 demand data from AEMO and caches it in memory.

Strategy:
  - Use AEMO's Daily_Reports endpoint: one ZIP per day, covers ~60 days.
  - Each file contains full 5-min DREGION data for TAS1.
  - Fetch the last HISTORY_DAYS files, resample to hourly, cache in-process.
  - Refresh every CACHE_TTL_SECONDS via background task.
  - Fall back to bundled CSV if all AEMO fetches fail.
"""

import io
import logging
import re
import urllib.request
import zipfile
from datetime import date, timedelta, datetime, timezone
from pathlib import Path
from threading import Lock

import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

HISTORY_DAYS = 30
CACHE_TTL_SECONDS = 3600

DAILY_REPORTS_INDEX = "https://nemweb.com.au/Reports/Current/Daily_Reports/"

# ── In-memory cache ────────────────────────────────────────────────────────────

_cache_lock = Lock()
_cached_df: pd.DataFrame | None = None
_cached_at: datetime | None = None


# ── AEMO fetch helpers ─────────────────────────────────────────────────────────

def _fetch_zip_csv(url: str, timeout: int = 30) -> bytes | None:
    """Download a ZIP from AEMO and return the first file's bytes."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            return zf.read(zf.namelist()[0])
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None


def _parse_daily_report(csv_bytes: bytes) -> pd.DataFrame:
    """
    Parse a Daily_Reports file — extracts TAS1 demand from DREGION rows.
    Column layout: row_type, table, sub, version, SETTLEMENTDATE, RUNNO,
                   REGIONID, INTERVENTION, ..., TOTALDEMAND (index 12)
    """
    lines = csv_bytes.decode("utf-8", errors="replace").splitlines()
    data_lines = [l for l in lines if l.startswith("D,DREGION") and "TAS1" in l]
    if not data_lines:
        return pd.DataFrame()

    rows = []
    for line in data_lines:
        parts = line.split(",")
        try:
            # Skip intervention runs (col 7 == "1")
            if parts[7].strip() not in ("0", "0.0"):
                continue
            timestamp = pd.to_datetime(parts[4].strip('"'), format="%Y/%m/%d %H:%M:%S")
            demand_mw = float(parts[13])
            rows.append({"timestamp": timestamp, "demand_mw": demand_mw, "region": "TAS"})
        except (IndexError, ValueError):
            continue

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _fetch_live() -> pd.DataFrame | None:
    """
    Fetch the last HISTORY_DAYS of TAS1 demand from AEMO Daily_Reports.
    One ZIP file per day — fast and reliable.
    """
    # Get the index page
    try:
        req = urllib.request.Request(
            DAILY_REPORTS_INDEX, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            index_html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning("Failed to fetch Daily_Reports index: %s", e)
        return None

    # Parse all unique daily filenames and sort
    # Format: PUBLIC_DAILY_YYYYMMDD0000_timestamp.zip
    file_map: dict[str, str] = {}
    for fname in re.findall(r'PUBLIC_DAILY_\d{12}_\d+\.zip', index_html):
        day_key = fname[13:21]  # YYYYMMDD portion
        file_map[day_key] = fname  # last one wins (latest version for that day)

    if not file_map:
        logger.warning("No files found in Daily_Reports index")
        return None

    # Select the last HISTORY_DAYS worth of files
    today = date.today()
    cutoff = today - timedelta(days=HISTORY_DAYS)
    selected = sorted(
        [(day_key, fname) for day_key, fname in file_map.items()
         if day_key >= cutoff.strftime("%Y%m%d")],
        key=lambda x: x[0]
    )

    logger.info("Fetching %d daily AEMO files (last %d days)", len(selected), HISTORY_DAYS)

    frames = []
    for day_key, fname in selected:
        url = DAILY_REPORTS_INDEX + fname
        csv_bytes = _fetch_zip_csv(url)
        if csv_bytes:
            df = _parse_daily_report(csv_bytes)
            if not df.empty:
                frames.append(df)
                logger.info("  %s: %d rows", day_key, len(df))

    if not frames:
        return None

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("timestamp").drop_duplicates("timestamp")

    # Resample 5-min → hourly
    combined = combined.set_index("timestamp")
    hourly = combined["demand_mw"].resample("h").mean().round(2).reset_index()
    hourly["region"] = "TAS"
    return hourly


def _load_csv_fallback() -> pd.DataFrame:
    """Load bundled CSV as fallback when AEMO is unreachable."""
    path = Path(settings.data_path)
    if not path.exists():
        raise FileNotFoundError(f"No fallback CSV at {path} and AEMO fetch failed.")
    logger.warning("Using CSV fallback: %s", path)
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["demand_mw"] = pd.to_numeric(df["demand_mw"], errors="coerce")
    return df.dropna(subset=["demand_mw", "timestamp"])


# ── Public API ─────────────────────────────────────────────────────────────────

def refresh_data() -> None:
    """Fetch fresh AEMO data and update the in-memory cache."""
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
    """Return the cached DataFrame, fetching if cache is empty."""
    with _cache_lock:
        df = _cached_df

    if df is None:
        refresh_data()
        with _cache_lock:
            df = _cached_df

    if df is None:
        raise RuntimeError("No data available — AEMO unreachable and no fallback CSV.")

    return df


def get_recent_window(hours: int = 168) -> pd.DataFrame:
    """Return the most recent N hours of data."""
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
    """Return seconds since cache was last updated, or None if never."""
    with _cache_lock:
        cached_at = _cached_at
    if cached_at is None:
        return None
    return (datetime.now(timezone.utc) - cached_at).total_seconds()
