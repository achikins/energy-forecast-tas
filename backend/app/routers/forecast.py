"""
Router: GET /forecast

Returns demand forecast for the next N hours using Holt-Winters
exponential smoothing. Includes per-point confidence bounds.

Query params:
  - periods: number of hours to forecast (default 48, max 168)
"""

from fastapi import APIRouter, HTTPException, Query

from app.models.forecast import ForecastResponse
from app.services.forecast_service import generate_forecast

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("", response_model=ForecastResponse)
def get_forecast(
    periods: int = Query(48, ge=1, le=168, description="Hours to forecast ahead"),
):
    try:
        return generate_forecast(periods=periods)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast failed: {e}")
