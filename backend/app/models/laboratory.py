import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class LabStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"


class Laboratory(Base):
    __tablename__ = "laboratories"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    location: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[LabStatus] = mapped_column(Enum(LabStatus), default=LabStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    required_skills = relationship("LabSkill", back_populates="laboratory", cascade="all, delete-orphan")
    equipment = relationship("LabEquipment", back_populates="laboratory", cascade="all, delete-orphan")
    time_slots = relationship("LabTimeSlot", back_populates="laboratory", cascade="all, delete-orphan")
    preferences = relationship("StudentPreference", back_populates="laboratory")
    allocations = relationship("Allocation", back_populates="laboratory")


class LabSkill(Base):
    """Subject / skill requirements a student must satisfy to be eligible for a lab."""

    __tablename__ = "lab_skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    lab_id: Mapped[int] = mapped_column(ForeignKey("laboratories.id", ondelete="CASCADE"), index=True)
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    min_proficiency: Mapped[int] = mapped_column(Integer, default=1)
    required: Mapped[bool] = mapped_column(Boolean, default=True)

    laboratory = relationship("Laboratory", back_populates="required_skills")


class LabEquipment(Base):
    __tablename__ = "lab_equipment"

    id: Mapped[int] = mapped_column(primary_key=True)
    lab_id: Mapped[int] = mapped_column(ForeignKey("laboratories.id", ondelete="CASCADE"), index=True)
    equipment_name: Mapped[str] = mapped_column(String(150), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    laboratory = relationship("Laboratory", back_populates="equipment")


class LabTimeSlot(Base):
    """Availability windows for a laboratory used for scheduling-conflict constraints."""

    __tablename__ = "lab_time_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    lab_id: Mapped[int] = mapped_column(ForeignKey("laboratories.id", ondelete="CASCADE"), index=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon .. 6=Sun
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "HH:MM"
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    laboratory = relationship("Laboratory", back_populates="time_slots")
