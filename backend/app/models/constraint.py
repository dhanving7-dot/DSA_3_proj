import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class ConstraintType(str, enum.Enum):
    ELIGIBILITY = "ELIGIBILITY"
    PRIORITY = "PRIORITY"
    SCHEDULING = "SCHEDULING"
    FAIRNESS = "FAIRNESS"
    CAPACITY = "CAPACITY"


class Constraint(Base):
    """Configurable rules that shape how the matching engine builds the bipartite graph."""

    __tablename__ = "constraints"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    type: Mapped[ConstraintType] = mapped_column(Enum(ConstraintType), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
