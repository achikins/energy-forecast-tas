"""
Fetches real energy demand data for Tasmania (TAS1) from AEMO NEM archives.

Source: Australian Energy Market Operator (AEMO) — nemweb.com.au
Table:  DISPATCHREGIONSUM — 5-minute dispatch intervals
Region: TAS1 (Tasmania)

Usage:
    python data/fetch_aemo_data.py

Output:
    data/energy_demand.csv  (replaces synthetic dataset)

Data format from AEMO:
  - Each row starts with a row-type character (I=header, D=data, C=end)
  - 5-minute intervals, 288 periods per day
  - Timestamps in AEMO market time (UTC+10, no DST)
  - TOTALDEMAND column = regional demand in MW
"""

import io
import zipfile
from datetime import date, timedelta

import pandas as pd
import urllib.request

# ── Configuration ─────────────────────────────────────────────────────────────

# Fetch this many months back from today (6 months ≈ 26,000 rows of 5-min data)
MONTHS_BACK = 6

# Output file (relative to this script's directory)
OUTPUT_FILE = "energy_demand.csv"

# AEMO archive URL template
ARCHIVE_URL = (
    "https://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/"
    "{year}/MMSDM_{year}_{month:02d}/MMSDM_Historical_Data_SQLLoader/DATA/"
    "PUBLIC_ARCHIVE%23DISPATCHREGIONSUM%23FILE01%23{year}{month:02d}010000.zip"
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def month_range(months_back: int) -> list[tuple[int, int]]:
    """Return (year, month) tuples for the last N calendar months."""
    today = date.today()
    result = []
    # Step back month by month
    y, m = today.year, today.month
    for _ in range(months_back):
        m -= 1
        if m == 0:
            m = 12
            y -= 1
        result.append((y, m))
    return list(reversed(result))


def fetch_month(year: int, month: int) -> pd.DataFrame | None:
    """
    Download and parse one month of DISPATCHREGIONSUM data for TAS1.
    Returns a DataFrame with columns [timestamp, demand_mw] or None on failure.
    """
    url = ARCHIVE_URL.format(year=year, month=month)
    print(f"  Fetching {year}-{month:02d} ... ", end="", flush=True)

    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            raw = resp.read()
    except Exception as e:
        print(f"FAILED ({e})")
        return None

    # The ZIP contains a single CSV file
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            csv_name = zf.namelist()[0]
            csv_bytes = zf.read(csv_name)
    except Exception as e:
        print(f"ZIP error ({e})")
        return None

    # AEMO CSV structure: rows start with I (header), D (data), or C (end-of-file)
    # We only want D rows for the DISPATCHREGIONSUM report
    lines = csv_bytes.decode("utf-8", errors="replace").splitlines()
    data_lines = [l for l in lines if l.startswith("D,DISPATCH,REGIONSUM")]

    if not data_lines:
        print("no data rows")
        return None

    # Parse into DataFrame using the I-row header to name columns
    header_lines = [l for l in lines if l.startswith("I,DISPATCH,REGIONSUM")]
    if header_lines:
        cols = header_lines[0].split(",")
    else:
        # Fallback: use positional names
        cols = None

    df = pd.read_csv(io.StringIO("\n".join(data_lines)), header=None, names=cols)

    # Normalise column names to uppercase (AEMO headers are already uppercase)
    df.columns = [str(c).strip().upper() for c in df.columns]

    # Filter: Tasmania only, non-intervention runs
    df = df[(df["REGIONID"] == "TAS1") & (df["INTERVENTION"] == 0)].copy()

    if df.empty:
        print("no TAS1 rows")
        return None

    # Parse timestamp
    df["timestamp"] = pd.to_datetime(df["SETTLEMENTDATE"], format="%Y/%m/%d %H:%M:%S")
    df["demand_mw"] = pd.to_numeric(df["TOTALDEMAND"], errors="coerce")
    df["region"] = "TAS"

    result = df[["timestamp", "demand_mw", "region"]].dropna().copy()
    print(f"OK ({len(result):,} rows)")
    return result


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    months = month_range(MONTHS_BACK)
    print(f"Fetching AEMO TAS1 data for {len(months)} months: "
          f"{months[0][0]}-{months[0][1]:02d} → {months[-1][0]}-{months[-1][1]:02d}")
    print()

    frames = []
    for year, month in months:
        df = fetch_month(year, month)
        if df is not None:
            frames.append(df)

    if not frames:
        print("\nERROR: No data could be fetched.")
        return

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("timestamp").drop_duplicates("timestamp")

    # Resample to hourly by taking the mean of the 12 x 5-min intervals per hour
    combined = combined.set_index("timestamp")
    hourly = combined["demand_mw"].resample("h").mean().round(2).reset_index()
    hourly["region"] = "TAS"
    hourly["timestamp"] = hourly["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    import pathlib
    out = pathlib.Path(__file__).parent / OUTPUT_FILE
    hourly.to_csv(out, index=False)

    print(f"\nSaved {len(hourly):,} hourly rows to {out}")
    print(f"Date range: {hourly['timestamp'].iloc[0]} → {hourly['timestamp'].iloc[-1]}")
    print(f"Demand range: {hourly['demand_mw'].min():.0f} – {hourly['demand_mw'].max():.0f} MW")


if __name__ == "__main__":
    main()
