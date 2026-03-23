"""Pydantic models for the Energy Decision Layer output."""

from pydantic import BaseModel


class BestUsageWindow(BaseModel):
    start_hour: int          # 0-23
    end_hour: int            # 0-23
    label: str               # e.g. "02:00 – 06:00"
    avg_demand_mw: float     # expected average demand during this window
    reason: str              # plain-text explanation


class PeakGenerationWindow(BaseModel):
    start_hour: int
    end_hour: int
    label: str
    expected_demand_mw: float   # demand proxy for generation pressure
    confidence: str             # "high" | "medium" | "low"
    note: str


class DecisionSummary(BaseModel):
    best_usage_windows: list[BestUsageWindow]    # top 3 low-demand periods (next 48h)
    peak_generation_windows: list[PeakGenerationWindow]  # expected peak generation hours
    advice: str                                  # one-line actionable advice
    generated_at: str
