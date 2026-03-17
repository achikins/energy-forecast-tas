"""Pydantic models for historical demand data."""

from pydantic import BaseModel


class DemandRecord(BaseModel):
    timestamp: str
    demand_mw: float
    region: str


class HistoricalResponse(BaseModel):
    data: list[DemandRecord]
    total_records: int
    start: str
    end: str
