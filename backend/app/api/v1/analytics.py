from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.analytics import AnalyticsOverview
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def overview(run_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return analytics_service.get_full_analytics(db, run_id)


@router.get("/lab-utilization")
def lab_utilization(run_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return analytics_service.get_lab_utilization(db, run_id)


@router.get("/departments")
def department_allocation(run_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return analytics_service.get_department_allocation(db, run_id)


@router.get("/algorithm-performance")
def algorithm_performance(limit: int = 20, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return analytics_service.get_algorithm_performance(db, limit)


@router.get("/history")
def history(limit: int = 20, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return analytics_service.get_historical_runs(db, limit)
