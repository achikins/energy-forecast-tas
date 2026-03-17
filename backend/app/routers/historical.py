"""
Router: GET /historical

Returns paginated historical demand data with optional date range filtering.
Query params:
  - start: ISO date string (optional)
  - end:   ISO date string (optional)
  - limit: max records to return (default 168 = 7 days hourly)
"""

from fastapi import APIRouter, HTTPException, Query

from app.models.demand import DemandRecord, HistoricalResponse
from app.services.data_service import get_date_range

router = APIRouter(prefix="/historical", tags=["historical"])


@router.get("", response_model=HistoricalResponse)
def get_historical(
    start: str | None = Query(None, description="Start datetime, e.g. 2023-06-01"),
    end: str | None = Query(None, description="End datetime, e.g. 2023-06-30"),
    limit: int = Query(168, ge=1, le=8760, description="Max number of records"),
):
    try:
        df = get_date_range(start, end)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if df.empty:
        raise HTTPException(status_code=404, detail="No data found for the given range.")

    df = df.tail(limit)

    records = [
        DemandRecord(
            timestamp=row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            demand_mw=round(row["demand_mw"], 2),
            region=row["region"],
        )
        for _, row in df.iterrows()
    ]

    return HistoricalResponse(
        data=records,
        total_records=len(records),
        start=records[0].timestamp,
        end=records[-1].timestamp,
    )
