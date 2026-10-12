import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AlgorithmName(str, enum.Enum):
    KUHN = "KUHN"
    HOPCROFT_KARP = "HOPCROFT_KARP"
    EDMONDS_KARP = "EDMONDS_KARP"
    DINIC = "DINIC"
    FORD_FULKERSON = "FORD_FULKERSON"
    MIN_COST_FLOW = "MIN_COST_FLOW"


class RunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AllocationStatus(str, enum.Enum):
    MATCHED = "MATCHED"
    UNMATCHED = "UNMATCHED"


class AllocationRun(Base):
    __tablename__ = "allocation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    algorithm: Mapped[AlgorithmName] = mapped_column(Enum(AlgorithmName), nullable=False)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.PENDING)
    total_students: Mapped[int] = mapped_column(Integer, default=0)
    total_labs: Mapped[int] = mapped_column(Integer, default=0)
    total_edges: Mapped[int] = mapped_column(Integer, default=0)
    matched_count: Mapped[int] = mapped_column(Integer, default=0)
    unmatched_count: Mapped[int] = mapped_column(Integer, default=0)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    preference_satisfaction: Mapped[float] = mapped_column(Float, default=0.0)
    capacity_utilization: Mapped[float] = mapped_column(Float, default=0.0)
    config_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    allocations = relationship("Allocation", back_populates="run", cascade="all, delete-orphan")
    metrics = relationship("AlgorithmMetric", back_populates="run", uselist=False, cascade="all, delete-orphan")


class Allocation(Base):
    __tablename__ = "allocations"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("allocation_runs.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    lab_id: Mapped[int | None] = mapped_column(ForeignKey("laboratories.id", ondelete="SET NULL"), nullable=True)
    algorithm: Mapped[AlgorithmName] = mapped_column(Enum(AlgorithmName), nullable=False)
    preference_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    eligibility_reason: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[AllocationStatus] = mapped_column(Enum(AllocationStatus), default=AllocationStatus.UNMATCHED)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run = relationship("AllocationRun", back_populates="allocations")
    student = relationship("Student", back_populates="allocations")
    laboratory = relationship("Laboratory", back_populates="allocations")


class AlgorithmMetric(Base):
    """Per-run algorithmic performance data, surfaced in the analytics + playground UI."""

    __tablename__ = "algorithm_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("allocation_runs.id", ondelete="CASCADE"), index=True)
    algorithm: Mapped[AlgorithmName] = mapped_column(Enum(AlgorithmName), nullable=False)
    vertices: Mapped[int] = mapped_column(Integer, default=0)
    edges: Mapped[int] = mapped_column(Integer, default=0)
    iterations: Mapped[int] = mapped_column(Integer, default=0)
    augmenting_paths_found: Mapped[int] = mapped_column(Integer, default=0)
    time_complexity: Mapped[str] = mapped_column(String(100), default="")
    space_complexity: Mapped[str] = mapped_column(String(100), default="")
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run = relationship("AllocationRun", back_populates="metrics")
