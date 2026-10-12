from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    roll_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    cgpa: Mapped[float] = mapped_column(Float, default=0.0)
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)  # used for fairness/priority constraints
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="student_profile")
    skills = relationship("StudentSkill", back_populates="student", cascade="all, delete-orphan")
    preferences = relationship(
        "StudentPreference", back_populates="student", cascade="all, delete-orphan",
        order_by="StudentPreference.rank",
    )
    allocations = relationship("Allocation", back_populates="student")


class StudentSkill(Base):
    __tablename__ = "student_skills"
    __table_args__ = (UniqueConstraint("student_id", "skill_name", name="uq_student_skill"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    proficiency_level: Mapped[int] = mapped_column(Integer, default=1)  # 1-5

    student = relationship("Student", back_populates="skills")


class StudentPreference(Base):
    __tablename__ = "student_preferences"
    __table_args__ = (
        UniqueConstraint("student_id", "lab_id", name="uq_student_lab_pref"),
        UniqueConstraint("student_id", "rank", name="uq_student_rank"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    lab_id: Mapped[int] = mapped_column(ForeignKey("laboratories.id", ondelete="CASCADE"), index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 = most preferred
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="preferences")
    laboratory = relationship("Laboratory", back_populates="preferences")
