from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin_or_faculty
from app.models.allocation import AllocationRun
from app.models.user import User
from app.schemas.allocation import (
    AllocationRunDetail,
    AllocationRunOut,
    GenerateAllocationRequest,
    SimulateAllocationRequest,
)
from app.services import allocation_service, audit_service, simulation_service
from app.ws.manager import manager, replay_steps

router = APIRouter(prefix="/allocation", tags=["allocation"])


@router.post("/generate", response_model=AllocationRunDetail)
async def generate_allocation(
    payload: GenerateAllocationRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty),
):
    result, _, _ = allocation_service.compute_engine_result(
        db, payload.algorithm.value, payload.config, payload.student_ids, payload.lab_ids
    )

    if payload.stream_progress:
        channel = "run:pending"
        await manager.broadcast(channel, {"type": "RUN_STARTED", "algorithm": payload.algorithm.value})
        await replay_steps(channel, [s.to_dict() for s in result.algorithm_trace.steps])

    run = allocation_service.persist_allocation_run(db, payload.algorithm.value, payload.config, result, current_user.id)

    if payload.stream_progress:
        await manager.broadcast("run:pending", {"type": "ALGORITHM_COMPLETE", "run_id": run.id})
        await manager.broadcast(f"run:{run.id}", {"type": "ALGORITHM_COMPLETE", "run_id": run.id})

    audit_service.log_action(
        db,
        current_user.id,
        "GENERATE_ALLOCATION",
        "AllocationRun",
        str(run.id),
        {"algorithm": payload.algorithm.value, "matched": run.matched_count, "unmatched": run.unmatched_count},
        request.client.host if request.client else "",
    )

    return _load_run_detail(db, run.id)


def _load_run_detail(db: Session, run_id: int) -> AllocationRun:
    run = (
        db.query(AllocationRun)
        .options(selectinload(AllocationRun.allocations), selectinload(AllocationRun.metrics))
        .filter(AllocationRun.id == run_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Allocation run not found")
    return run


@router.get("/runs", response_model=list[AllocationRunOut])
def list_runs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return (
        db.query(AllocationRun)
        .options(selectinload(AllocationRun.metrics))
        .order_by(AllocationRun.created_at.desc(), AllocationRun.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/runs/{run_id}", response_model=AllocationRunDetail)
def get_run(run_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return _load_run_detail(db, run_id)


@router.post("/simulate")
def simulate(
    payload: SimulateAllocationRequest, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return simulation_service.simulate_allocation(db, payload)
