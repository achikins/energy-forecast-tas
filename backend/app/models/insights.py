"""Pydantic models for insights and analytics output."""

from pydantic import BaseModel


class AnomalyRecord(BaseModel):
    timestamp: str
    demand_mw: float
    deviation_pct: float
    description: str


class PeakPeriod(BaseModel):
    timestamp: str
    demand_mw: float
    hour_of_day: int
    day_of_week: str


class InsightsSummary(BaseModel):
    average_demand_mw: float
    peak_demand_mw: float
    peak_timestamp: str
    min_demand_mw: float
    min_timestamp: str
    demand_trend: str          # "rising", "falling", "stable"
    trend_change_pct: float    # % change over the analysis window
    anomalies: list[AnomalyRecord]
    top_peak_periods: list[PeakPeriod]
    summary_text: str          # human-readable narrative
