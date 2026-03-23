"""Router for the Energy Decision Layer endpoint."""

from fastapi import APIRouter, HTTPException

from app.models.decision import DecisionSummary
from app.services.decision_service import compute_decision

router = APIRouter(tags=["decision"])


@router.get("/decision", response_model=DecisionSummary)
def get_decision():
    """
    Return best times to use energy and expected peak generation windows
    for the next 48 hours, derived from the demand forecast.
    """
    try:
        return compute_decision()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
