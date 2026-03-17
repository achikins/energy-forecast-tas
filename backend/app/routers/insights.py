"""
Router: GET /insights

Returns analytical insights over a rolling window of historical data.
Includes peak demand, trend direction, anomaly detection, and a narrative summary.

Query params:
  - hours: analysis window in hours (default 168 = 7 days)
"""

from fastapi import APIRouter, HTTPException, Query

from app.models.insights import InsightsSummary
from app.services.insights_service import compute_insights

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("", response_model=InsightsSummary)
def get_insights(
    hours: int = Query(168, ge=24, le=8760, description="Analysis window in hours"),
):
    try:
        return compute_insights(hours=hours)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insights computation failed: {e}")
