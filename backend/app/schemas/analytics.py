from pydantic import BaseModel


class OverviewStats(BaseModel):
    total_students: int
    total_labs: int
    total_capacity: int
    matched_students: int
    unmatched_students: int
    matching_percentage: float
    capacity_utilization: float
    preference_satisfaction: float
    latest_run_id: int | None = None
    latest_algorithm: str | None = None


class LabUtilization(BaseModel):
    lab_id: int
    lab_name: str
    department: str
    capacity: int
    allocated: int
    utilization: float


class DepartmentAllocation(BaseModel):
    department: str
    total_students: int
    matched: int
    unmatched: int


class AlgorithmPerformance(BaseModel):
    algorithm: str
    run_id: int
    vertices: int
    edges: int
    execution_time_ms: float
    matched_count: int
    iterations: int


class HistoricalRun(BaseModel):
    run_id: int
    algorithm: str
    status: str
    matched_count: int
    unmatched_count: int
    execution_time_ms: float
    created_at: str


class AnalyticsOverview(BaseModel):
    overview: OverviewStats
    lab_utilization: list[LabUtilization]
    department_allocation: list[DepartmentAllocation]
    algorithm_performance: list[AlgorithmPerformance]
    historical_runs: list[HistoricalRun]
