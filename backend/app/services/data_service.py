"""
Data service — fetches live TAS1 demand data from AEMO and caches it in memory.

Strategy:
  - Past completed months: AEMO monthly DISPATCHREGIONSUM archive ZIPs.
  - Current (incomplete) month: scrape individual 5-min Dispatch_Reports files.
  - Combine, resample to hourly, cache in-process.
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

# Monthly archive — only published once a month is fully complete
ARCHIVE_URL = (
    "https://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/"
    "{year}/MMSDM_{year}_{month:02d}/MMSDM_Historical_Data_SQLLoader/DATA/"
    "PUBLIC_ARCHIVE%23DISPATCHREGIONSUM%23FILE01%23{year}{month:02d}010000.zip"
)

# Current-month 5-min dispatch files index (rolling ~2 days, updated every 5 min)
DISPATCH_REPORTS_INDEX = "https://nemweb.com.au/Reports/Current/Dispatch_Reports/"

# ── In-memory cache ────────────────────────────────────────────────────────────

_cache_lock = Lock()
_cached_df: pd.DataFrame | None = None
_cached_at: datetime | None = None


# ── AEMO fetch helpers ─────────────────────────────────────────────────────────

def _fetch_zip_csv(url: str, timeout: int = 60) -> bytes | None:
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


def _parse_dispatchregionsum(csv_bytes: bytes) -> pd.DataFrame:
    """Parse AEMO DISPATCHREGIONSUM archive CSV → clean TAS1 DataFrame."""
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


def _parse_dispatch_report(csv_bytes: bytes) -> pd.DataFrame:
    """
    Parse a 5-min Dispatch_Reports file (DREGION table) → TAS1 demand row.
    Column order: SETTLEMENTDATE, INTERVENTION, REGIONID, ..., TOTALDEMAND (index 8)
    """
    lines = csv_bytes.decode("utf-8", errors="replace").splitlines()
    data_lines = [l for l in lines if l.startswith("D,DREGION") and "TAS1" in l]
    if not data_lines:
        return pd.DataFrame()

    rows = []
    for line in data_lines:
        parts = line.split(",")
        # Filter: intervention == 0
        try:
            if parts[6] != "0" and parts[6] != "0.0":
                continue
            timestamp = pd.to_datetime(parts[4].strip('"'), format="%Y/%m/%d %H:%M:%S")
            demand_mw = float(parts[8])
            rows.append({"timestamp": timestamp, "demand_mw": demand_mw, "region": "TAS"})
        except (IndexError, ValueError):
            continue

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _fetch_archive_month(year: int, month: int) -> pd.DataFrame:
    """Fetch a completed month from the AEMO monthly archive."""
    url = ARCHIVE_URL.format(year=year, month=month)
    logger.info("Fetching AEMO archive %d-%02d", year, month)
    csv_bytes = _fetch_zip_csv(url)
    if csv_bytes is None:
        return pd.DataFrame()
    return _parse_dispatchregionsum(csv_bytes)


def _fetch_current_month_dispatch() -> pd.DataFrame:
    """
    Scrape all 5-min Dispatch_Reports files from AEMO's rolling index.
    Covers roughly the last 2 days (all that AEMO keeps in this endpoint).
    """
    logger.info("Fetching current-month dispatch files from Dispatch_Reports index")
    try:
        req = urllib.request.Request(
            DISPATCH_REPORTS_INDEX, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            index_html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning("Failed to fetch Dispatch_Reports index: %s", e)
        return pd.DataFrame()

    # Extract unique ZIP filenames
    filenames = list(dict.fromkeys(
        re.findall(r'PUBLIC_DISPATCH_\d+_\d+_LEGACY\.zip', index_html)
    ))
    logger.info("Found %d dispatch report files", len(filenames))

    frames = []
    for fname in filenames:
        url = DISPATCH_REPORTS_INDEX + fname
        csv_bytes = _fetch_zip_csv(url, timeout=15)
        if csv_bytes:
            df = _parse_dispatch_report(csv_bytes)
            if not df.empty:
                frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    return combined.drop_duplicates("timestamp")


def _fetch_live() -> pd.DataFrame | None:
    """
    Fetch HISTORY_DAYS of TAS1 demand.
    - Completed past months: monthly archive
    - Current month: Dispatch_Reports 5-min files
    """
    today = date.today()
    frames = []

    # Determine which months we need
    months_needed: dict[tuple[int, int], bool] = {}  # (year, month) → is_current
    for d in range(HISTORY_DAYS + 1):
        day = today - timedelta(days=d)
        key = (day.year, day.month)
        is_current = (day.year == today.year and day.month == today.month)
        # Mark as current if any day in that month is the current month
        months_needed[key] = months_needed.get(key, False) or is_current

    for (year, month), is_current in sorted(months_needed.items()):
        if is_current:
            # Use rolling 5-min dispatch files for current month
            df = _fetch_current_month_dispatch()
        else:
            df = _fetch_archive_month(year, month)

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
