from pydantic import BaseModel

from app.schemas.constraint import AllocationConfig


class AICommandRequest(BaseModel):
    text: str
    auto_execute: bool = False  # if True, immediately run the allocation with the parsed config


class ParsedConstraints(BaseModel):
    algorithm: str
    config: AllocationConfig
    department_filter: str | None = None
    year_filter: int | None = None
    lab_name_filters: list[str] = []
    notes: list[str] = []


class AICommandResponse(BaseModel):
    original_text: str
    parsed: ParsedConstraints
    matched_student_count: int
    matched_lab_count: int
    executed: bool
    run_id: int | None = None
    message: str


class AIExplainRequest(BaseModel):
    allocation_id: int | None = None
    student_id: int | None = None
    run_id: int | None = None


class AIExplainResponse(BaseModel):
    student_id: int
    lab_id: int | None
    status: str
    explanation: str
    facts: dict


class AIAnalyticsQueryRequest(BaseModel):
    question: str
    run_id: int | None = None


class AIAnalyticsQueryResponse(BaseModel):
    question: str
    answer: str
    facts: dict
