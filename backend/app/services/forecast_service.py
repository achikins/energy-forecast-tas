"""
Forecast service — generates demand predictions using Holt-Winters
Exponential Smoothing (triple exponential smoothing with seasonal component).

This is a solid, interpretable forecasting method that performs well on
energy time-series data without the overhead of full ML infrastructure.
It captures trend and daily seasonality (period=24 for hourly data).
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone

from statsmodels.tsa.holtwinters import ExponentialSmoothing

from app.models.forecast import ForecastPoint, ForecastResponse
from app.services.data_service import get_dataframe


# Confidence interval width (z * std of residuals)
_CI_Z = 1.645  # ~90% confidence interval


def generate_forecast(periods: int = 48) -> ForecastResponse:
    """
    Fit a Holt-Winters model on the most recent 30 days of hourly data
    and produce `periods` hours of forward predictions with confidence bands.
    """
    df = get_dataframe()

    # Use the last 30 days for fitting — enough seasonal cycles without
    # over-weighting old data in a stable-pattern series
    training_window = df.tail(30 * 24).copy()
    series = training_window.set_index("timestamp")["demand_mw"]

    # Holt-Winters: additive trend + additive seasonality (period=24 hours)
    model = ExponentialSmoothing(
        series,
        trend="add",
        seasonal="add",
        seasonal_periods=24,
        initialization_method="estimated",
    )
    fitted = model.fit(optimized=True, remove_bias=True)

    # Point forecasts
    forecast_values = fitted.forecast(periods)

    # Residual-based confidence interval
    residuals = fitted.resid
    residual_std = residuals.std()
    margin = _CI_Z * residual_std

    last_timestamp = series.index[-1]
    forecast_timestamps = pd.date_range(
        start=last_timestamp + pd.Timedelta(hours=1),
        periods=periods,
        freq="h",
    )

    points = [
        ForecastPoint(
            timestamp=ts.strftime("%Y-%m-%d %H:%M:%S"),
            predicted_mw=round(float(val), 2),
            lower_bound=round(float(max(0, val - margin)), 2),
            upper_bound=round(float(val + margin), 2),
        )
        for ts, val in zip(forecast_timestamps, forecast_values)
    ]

    return ForecastResponse(
        data=points,
        periods=periods,
        model_used="Holt-Winters Exponential Smoothing (additive trend + seasonality, period=24h)",
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )
