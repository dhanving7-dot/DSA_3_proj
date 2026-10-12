from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.allocation import Allocation
from app.models.user import User
from app.schemas.ai import (
    AIAnalyticsQueryRequest,
    AIAnalyticsQueryResponse,
    AICommandRequest,
    AICommandResponse,
    AIExplainRequest,
    AIExplainResponse,
)
from app.services import ai_service, allocation_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/command", response_model=AICommandResponse)
def ai_command(
    payload: AICommandRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    parsed = ai_service.parse_command(payload.text, db)
    student_ids, lab_ids = ai_service.resolve_filters_to_ids(
        db, parsed.department_filter, parsed.year_filter, parsed.lab_name_filters
    )
    students = allocation_service.load_students(db, student_ids)
    labs = allocation_service.load_labs(db, lab_ids)

    run_id = None
    executed = False
    if payload.auto_execute:
        run = allocation_service.generate_and_persist_allocation(
            db, parsed.algorithm, parsed.config, student_ids, lab_ids, current_user.id
        )
        run_id = run.id
        executed = True
        message = (
            f"Executed {parsed.algorithm} on {run.total_students} students and {run.total_labs} labs: "
            f"{run.matched_count} matched, {run.unmatched_count} unmatched."
        )
    else:
        message = (
            f"Parsed your request into {parsed.algorithm} with {len(students)} matching students and "
            f"{len(labs)} matching laboratories. Resend with auto_execute=true (or call /allocation/generate "
            f"with this config) to run the real allocation engine."
        )

    return AICommandResponse(
        original_text=payload.text,
        parsed=parsed,
        matched_student_count=len(students),
        matched_lab_count=len(labs),
        executed=executed,
        run_id=run_id,
        message=message,
    )


@router.post("/explain", response_model=AIExplainResponse)
def ai_explain(payload: AIExplainRequest, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    allocation = None
    if payload.allocation_id:
        allocation = db.get(Allocation, payload.allocation_id)
    elif payload.student_id and payload.run_id:
        allocation = (
            db.query(Allocation)
            .filter(Allocation.student_id == payload.student_id, Allocation.run_id == payload.run_id)
            .first()
        )
    if not allocation:
        raise HTTPException(status_code=404, detail="No matching allocation record found to explain")
    return ai_service.explain_assignment(db, allocation)


@router.post("/analytics-query", response_model=AIAnalyticsQueryResponse)
def ai_analytics_query(
    payload: AIAnalyticsQueryRequest, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    answer, facts = ai_service.answer_analytics_question(db, payload.question, payload.run_id)
    return AIAnalyticsQueryResponse(question=payload.question, answer=answer, facts=facts)


@router.get("/conflicts")
def ai_conflicts(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return {"conflicts": ai_service.detect_conflicts(db)}


@router.get("/report")
def ai_report(run_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return {"report_markdown": ai_service.generate_report(db, run_id)}
