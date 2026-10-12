from datetime import datetime

from pydantic import BaseModel

from app.models.constraint import ConstraintType


class ConstraintBase(BaseModel):
    name: str
    type: ConstraintType
    config: dict = {}
    is_active: bool = True


class ConstraintCreate(ConstraintBase):
    pass


class ConstraintUpdate(BaseModel):
    name: str | None = None
    config: dict | None = None
    is_active: bool | None = None


class ConstraintOut(ConstraintBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AllocationConfig(BaseModel):
    """The full configurable ruleset the allocation engine consumes for a run."""

    same_department_only: bool = False
    require_preference: bool = False
    min_preference_score: float = 0.3
    preference_weight: float = 0.5
    skill_weight: float = 0.3
    priority_weight: float = 0.2
    max_share_per_department: float | None = None
