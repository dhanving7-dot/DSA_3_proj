from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.allocation import Allocation, AlgorithmMetric, AllocationRun, AllocationStatus
from app.models.laboratory import Laboratory
from app.models.student import Student


def get_latest_run(db: Session) -> AllocationRun | None:
    return db.query(AllocationRun).order_by(AllocationRun.created_at.desc(), AllocationRun.id.desc()).first()


def get_overview(db: Session) -> dict:
    total_students = db.query(func.count(Student.id)).scalar() or 0
    total_labs = db.query(func.count(Laboratory.id)).scalar() or 0
    total_capacity = db.query(func.coalesce(func.sum(Laboratory.capacity), 0)).scalar() or 0

    latest_run = get_latest_run(db)
    if latest_run:
        matched = latest_run.matched_count
        unmatched = latest_run.unmatched_count
        matching_pct = round(matched / latest_run.total_students, 4) if latest_run.total_students else 0.0
        capacity_util = latest_run.capacity_utilization
        pref_sat = latest_run.preference_satisfaction
    else:
        matched = unmatched = 0
        matching_pct = capacity_util = pref_sat = 0.0

    return {
        "total_students": total_students,
        "total_labs": total_labs,
        "total_capacity": total_capacity,
        "matched_students": matched,
        "unmatched_students": unmatched,
        "matching_percentage": matching_pct,
        "capacity_utilization": capacity_util,
        "preference_satisfaction": pref_sat,
        "latest_run_id": latest_run.id if latest_run else None,
        "latest_algorithm": latest_run.algorithm.value if latest_run else None,
    }


def get_lab_utilization(db: Session, run_id: int | None = None) -> list[dict]:
    run = db.get(AllocationRun, run_id) if run_id else get_latest_run(db)
    labs = db.query(Laboratory).all()
    if not run:
        return [
            {
                "lab_id": lab.id,
                "lab_name": lab.name,
                "department": lab.department,
                "capacity": lab.capacity,
                "allocated": 0,
                "utilization": 0.0,
            }
            for lab in labs
        ]
    counts: dict[int, int] = {}
    rows = (
        db.query(Allocation.lab_id, func.count(Allocation.id))
        .filter(Allocation.run_id == run.id, Allocation.status == AllocationStatus.MATCHED)
        .group_by(Allocation.lab_id)
        .all()
    )
    counts = {lab_id: count for lab_id, count in rows}
    result = []
    for lab in labs:
        allocated = counts.get(lab.id, 0)
        utilization = round(allocated / lab.capacity, 4) if lab.capacity else 0.0
        result.append(
            {
                "lab_id": lab.id,
                "lab_name": lab.name,
                "department": lab.department,
                "capacity": lab.capacity,
                "allocated": allocated,
                "utilization": utilization,
            }
        )
    return result


def get_department_allocation(db: Session, run_id: int | None = None) -> list[dict]:
    run = db.get(AllocationRun, run_id) if run_id else get_latest_run(db)
    if not run:
        return []
    rows = (
        db.query(Student.department, Allocation.status, func.count(Allocation.id))
        .join(Allocation, Allocation.student_id == Student.id)
        .filter(Allocation.run_id == run.id)
        .group_by(Student.department, Allocation.status)
        .all()
    )
    by_dept: dict[str, dict[str, int]] = {}
    for department, status, count in rows:
        entry = by_dept.setdefault(department, {"matched": 0, "unmatched": 0})
        key = "matched" if status == AllocationStatus.MATCHED else "unmatched"
        entry[key] += count
    return [
        {
            "department": dept,
            "total_students": counts["matched"] + counts["unmatched"],
            "matched": counts["matched"],
            "unmatched": counts["unmatched"],
        }
        for dept, counts in by_dept.items()
    ]


def get_algorithm_performance(db: Session, limit: int = 20) -> list[dict]:
    rows = (
        db.query(AlgorithmMetric, AllocationRun)
        .join(AllocationRun, AlgorithmMetric.run_id == AllocationRun.id)
        .order_by(AllocationRun.created_at.desc(), AllocationRun.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "algorithm": metric.algorithm.value,
            "run_id": run.id,
            "vertices": metric.vertices,
            "edges": metric.edges,
            "execution_time_ms": metric.execution_time_ms,
            "matched_count": run.matched_count,
            "iterations": metric.iterations,
        }
        for metric, run in rows
    ]


def get_historical_runs(db: Session, limit: int = 20) -> list[dict]:
    runs = db.query(AllocationRun).order_by(AllocationRun.created_at.desc(), AllocationRun.id.desc()).limit(limit).all()
    return [
        {
            "run_id": run.id,
            "algorithm": run.algorithm.value,
            "status": run.status.value,
            "matched_count": run.matched_count,
            "unmatched_count": run.unmatched_count,
            "execution_time_ms": run.execution_time_ms,
            "created_at": run.created_at.isoformat(),
        }
        for run in runs
    ]


def get_full_analytics(db: Session, run_id: int | None = None) -> dict:
    return {
        "overview": get_overview(db),
        "lab_utilization": get_lab_utilization(db, run_id),
        "department_allocation": get_department_allocation(db, run_id),
        "algorithm_performance": get_algorithm_performance(db),
        "historical_runs": get_historical_runs(db),
    }
