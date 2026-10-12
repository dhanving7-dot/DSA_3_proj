"""What-If Simulator: runs the real matching engine twice (before/after a
hypothetical change) and returns a structured comparison. Nothing here is
persisted as an official AllocationRun - it is a sandbox on top of the same
deterministic engine used everywhere else.
"""
from __future__ import annotations

import copy

from sqlalchemy.orm import Session

from app.algorithms.matching_engine import EngineConstraints, LabInput, StudentInput, run_allocation
from app.schemas.allocation import SimulateAllocationRequest
from app.services.allocation_service import to_engine_constraints, load_labs, load_students


def _metrics_from_result(result, execution_time_ms: float) -> dict:
    return {
        "matched_count": result.matched_count,
        "unmatched_count": result.unmatched_count,
        "total_students": result.total_students,
        "total_labs": result.total_labs,
        "preference_satisfaction": result.preference_satisfaction,
        "capacity_utilization": result.capacity_utilization,
        "execution_time_ms": execution_time_ms,
    }


def _synthesize_extra_students(existing: list[StudentInput], count: int) -> list[StudentInput]:
    if count <= 0 or not existing:
        return []
    next_id = max((s.id for s in existing), default=0) + 100000  # offset to avoid colliding with real IDs
    departments = [s.department for s in existing] or ["CSE"]
    extras = []
    for i in range(count):
        dept = departments[i % len(departments)]
        extras.append(
            StudentInput(
                id=next_id + i,
                department=dept,
                year=2,
                cgpa=7.0,
                priority_score=0.4,
                skills={},
                preferences={},
            )
        )
    return extras


def simulate_allocation(db: Session, request: SimulateAllocationRequest) -> dict:
    students = load_students(db, request.student_ids)
    labs = load_labs(db, request.lab_ids)

    baseline_constraints = to_engine_constraints(request.baseline_config)
    baseline_result = run_allocation(students, labs, baseline_constraints, request.algorithm.value)

    modified_students = list(students) + _synthesize_extra_students(students, request.extra_student_count)
    modified_labs: list[LabInput] = []
    for lab in labs:
        new_lab = copy.deepcopy(lab)
        if lab.id in request.lab_capacity_overrides:
            new_lab.capacity = request.lab_capacity_overrides[lab.id]
        modified_labs.append(new_lab)

    modified_constraints = to_engine_constraints(request.modified_config)
    modified_result = run_allocation(modified_students, modified_labs, modified_constraints, request.algorithm.value)

    before = _metrics_from_result(baseline_result, baseline_result.algorithm_trace.execution_time_ms)
    after = _metrics_from_result(modified_result, modified_result.algorithm_trace.execution_time_ms)

    delta = {
        key: round(after[key] - before[key], 4)
        for key in ("matched_count", "unmatched_count", "preference_satisfaction", "capacity_utilization", "execution_time_ms")
    }

    return {
        "algorithm": request.algorithm.value,
        "before": before,
        "after": after,
        "delta": delta,
        "changes_applied": {
            "lab_capacity_overrides": request.lab_capacity_overrides,
            "extra_student_count": request.extra_student_count,
            "baseline_config": request.baseline_config.model_dump(),
            "modified_config": request.modified_config.model_dump(),
        },
    }
