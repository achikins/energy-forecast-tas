"""Pydantic models for forecast output."""

from pydantic import BaseModel, ConfigDict


class ForecastPoint(BaseModel):
    timestamp: str
    predicted_mw: float
    lower_bound: float
    upper_bound: float


class ForecastResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    data: list[ForecastPoint]
    periods: int
    model_used: str
    generated_at: str
