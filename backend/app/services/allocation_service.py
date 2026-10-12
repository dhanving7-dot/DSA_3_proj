"""Bridges SQLAlchemy models to the pure-python matching engine, and persists
the results of a real allocation run (as opposed to the playground, which
never touches student/lab tables).
"""
from __future__ import annotations

from sqlalchemy.orm import Session, selectinload

from app.algorithms.matching_engine import (
    EngineConstraints,
    EngineResult,
    LabInput,
    LabRequiredSkill,
    StudentInput,
    run_allocation,
)
from app.models.allocation import Allocation, AlgorithmMetric, AllocationRun, AllocationStatus, RunStatus
from app.models.laboratory import LabStatus, Laboratory
from app.models.student import Student
from app.schemas.constraint import AllocationConfig


def to_engine_constraints(config: AllocationConfig) -> EngineConstraints:
    return EngineConstraints(
        same_department_only=config.same_department_only,
        require_preference=config.require_preference,
        min_preference_score=config.min_preference_score,
        preference_weight=config.preference_weight,
        skill_weight=config.skill_weight,
        priority_weight=config.priority_weight,
        max_share_per_department=config.max_share_per_department,
    )


def load_students(db: Session, student_ids: list[int] | None = None) -> list[StudentInput]:
    query = db.query(Student).options(selectinload(Student.skills), selectinload(Student.preferences))
    if student_ids:
        query = query.filter(Student.id.in_(student_ids))
    students = query.all()
    return [
        StudentInput(
            id=s.id,
            department=s.department,
            year=s.year,
            cgpa=s.cgpa,
            priority_score=s.priority_score,
            skills={sk.skill_name: sk.proficiency_level for sk in s.skills},
            preferences={p.lab_id: p.rank for p in s.preferences},
        )
        for s in students
    ]


def load_labs(db: Session, lab_ids: list[int] | None = None) -> list[LabInput]:
    query = db.query(Laboratory).options(
        selectinload(Laboratory.required_skills), selectinload(Laboratory.time_slots)
    )
    if lab_ids:
        query = query.filter(Laboratory.id.in_(lab_ids))
    labs = query.all()
    return [
        LabInput(
            id=lab.id,
            department=lab.department,
            capacity=lab.capacity,
            is_active=lab.status == LabStatus.ACTIVE,
            required_skills=[
                LabRequiredSkill(rs.skill_name, rs.min_proficiency, rs.required) for rs in lab.required_skills
            ],
            has_available_slot=(len(lab.time_slots) == 0) or any(ts.is_available for ts in lab.time_slots),
        )
        for lab in labs
    ]


def compute_engine_result(
    db: Session,
    algorithm: str,
    config: AllocationConfig,
    student_ids: list[int] | None = None,
    lab_ids: list[int] | None = None,
) -> tuple[EngineResult, list[StudentInput], list[LabInput]]:
    students = load_students(db, student_ids)
    labs = load_labs(db, lab_ids)
    constraints = to_engine_constraints(config)
    result = run_allocation(students, labs, constraints, algorithm)
    return result, students, labs


def persist_allocation_run(
    db: Session,
    algorithm: str,
    config: AllocationConfig,
    result: EngineResult,
    created_by: int | None,
) -> AllocationRun:
    run = AllocationRun(
        algorithm=algorithm,
        status=RunStatus.COMPLETED,
        total_students=result.total_students,
        total_labs=result.total_labs,
        total_edges=result.total_edges,
        matched_count=result.matched_count,
        unmatched_count=result.unmatched_count,
        execution_time_ms=result.algorithm_trace.execution_time_ms,
        preference_satisfaction=result.preference_satisfaction,
        capacity_utilization=result.capacity_utilization,
        config_snapshot=config.model_dump(),
        created_by=created_by,
    )
    db.add(run)
    db.flush()

    for assignment in result.assignments:
        db.add(
            Allocation(
                run_id=run.id,
                student_id=assignment.student_id,
                lab_id=assignment.lab_id,
                algorithm=algorithm,
                preference_rank=assignment.preference_rank,
                match_score=assignment.match_score,
                eligibility_reason=assignment.eligibility_reason,
                status=AllocationStatus(assignment.status),
            )
        )

    trace = result.algorithm_trace
    db.add(
        AlgorithmMetric(
            run_id=run.id,
            algorithm=algorithm,
            vertices=trace.vertices,
            edges=trace.edges,
            iterations=trace.iterations,
            augmenting_paths_found=trace.augmenting_paths_found,
            time_complexity=trace.time_complexity,
            space_complexity=trace.space_complexity,
            execution_time_ms=trace.execution_time_ms,
        )
    )

    db.commit()
    db.refresh(run)
    return run


def generate_and_persist_allocation(
    db: Session,
    algorithm: str,
    config: AllocationConfig,
    student_ids: list[int] | None,
    lab_ids: list[int] | None,
    created_by: int | None,
) -> AllocationRun:
    result, _, _ = compute_engine_result(db, algorithm, config, student_ids, lab_ids)
    return persist_allocation_run(db, algorithm, config, result, created_by)
