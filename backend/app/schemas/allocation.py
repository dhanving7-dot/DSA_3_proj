from datetime import datetime

from pydantic import BaseModel

from app.models.allocation import AlgorithmName, AllocationStatus, RunStatus
from app.schemas.constraint import AllocationConfig


class GenerateAllocationRequest(BaseModel):
    algorithm: AlgorithmName = AlgorithmName.HOPCROFT_KARP
    config: AllocationConfig = AllocationConfig()
    student_ids: list[int] | None = None  # None = all students
    lab_ids: list[int] | None = None  # None = all labs
    stream_progress: bool = False  # if true, also broadcast steps over the run's websocket channel


class RunMatchingRequest(BaseModel):
    """Used by the Algorithm Playground: run directly on a generated/synthetic graph."""

    algorithm: AlgorithmName = AlgorithmName.KUHN
    num_left: int = 10
    num_right: int = 5
    edge_probability: float = 0.4
    seed: int | None = None


class CompareAlgorithmsRequest(BaseModel):
    config: AllocationConfig = AllocationConfig()
    student_ids: list[int] | None = None
    lab_ids: list[int] | None = None
    algorithms: list[AlgorithmName] = [
        AlgorithmName.KUHN,
        AlgorithmName.HOPCROFT_KARP,
        AlgorithmName.EDMONDS_KARP,
        AlgorithmName.DINIC,
        AlgorithmName.FORD_FULKERSON,
        AlgorithmName.MIN_COST_FLOW,
    ]


class SimulateAllocationRequest(BaseModel):
    algorithm: AlgorithmName = AlgorithmName.HOPCROFT_KARP
    baseline_config: AllocationConfig = AllocationConfig()
    modified_config: AllocationConfig = AllocationConfig()
    lab_capacity_overrides: dict[int, int] = {}
    extra_student_count: int = 0
    student_ids: list[int] | None = None
    lab_ids: list[int] | None = None


class AllocationOut(BaseModel):
    id: int
    run_id: int
    student_id: int
    lab_id: int | None
    algorithm: AlgorithmName
    preference_rank: int | None
    match_score: float
    eligibility_reason: str
    status: AllocationStatus
    created_at: datetime

    class Config:
        from_attributes = True


class AlgorithmMetricOut(BaseModel):
    algorithm: AlgorithmName
    vertices: int
    edges: int
    iterations: int
    augmenting_paths_found: int
    time_complexity: str
    space_complexity: str
    execution_time_ms: float

    class Config:
        from_attributes = True


class AllocationRunOut(BaseModel):
    id: int
    algorithm: AlgorithmName
    status: RunStatus
    total_students: int
    total_labs: int
    total_edges: int
    matched_count: int
    unmatched_count: int
    execution_time_ms: float
    preference_satisfaction: float
    capacity_utilization: float
    created_at: datetime
    metrics: AlgorithmMetricOut | None = None

    class Config:
        from_attributes = True


class AllocationRunDetail(AllocationRunOut):
    allocations: list[AllocationOut] = []
