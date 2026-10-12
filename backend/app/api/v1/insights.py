from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.concepts import MonteCarloRequest
from app.services import insights_service

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/bottleneck")
def bottleneck(run_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return insights_service.bottleneck_analysis(db, run_id)


@router.get("/set-cover")
def set_cover(run_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return insights_service.set_cover_analysis(db, run_id)


@router.get("/skill-supply")
def skill_supply(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return insights_service.skill_supply(db)


@router.get("/optimality-gap")
def optimality_gap(run_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return insights_service.optimality_gap(db, run_id)


@router.post("/monte-carlo")
def monte_carlo(payload: MonteCarloRequest, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return insights_service.monte_carlo_outages(
        db, payload.trials, payload.outage_probability, payload.seed, payload.algorithm.value, payload.run_id
    )


@router.get("/audit-sample")
def audit_sample(
    run_id: int | None = None,
    k: int = Query(default=10, ge=1, le=100),
    seed: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return insights_service.audit_sample(db, run_id, k, seed)
