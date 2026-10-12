from datetime import datetime

from pydantic import BaseModel, Field


class StudentSkillIn(BaseModel):
    skill_name: str
    proficiency_level: int = Field(ge=1, le=5, default=1)


class StudentSkillOut(StudentSkillIn):
    id: int

    class Config:
        from_attributes = True


class StudentPreferenceIn(BaseModel):
    lab_id: int
    rank: int = Field(ge=1)


class StudentPreferenceOut(StudentPreferenceIn):
    id: int

    class Config:
        from_attributes = True


class StudentBase(BaseModel):
    roll_number: str
    full_name: str
    email: str
    department: str
    year: int = Field(ge=1, le=5)
    cgpa: float = Field(ge=0, le=10, default=0.0)
    priority_score: float = Field(ge=0, le=1, default=0.0)


class StudentCreate(StudentBase):
    skills: list[StudentSkillIn] = []
    preferences: list[StudentPreferenceIn] = []


class StudentUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    department: str | None = None
    year: int | None = Field(default=None, ge=1, le=5)
    cgpa: float | None = Field(default=None, ge=0, le=10)
    priority_score: float | None = Field(default=None, ge=0, le=1)


class StudentOut(StudentBase):
    id: int
    created_at: datetime
    skills: list[StudentSkillOut] = []
    preferences: list[StudentPreferenceOut] = []

    class Config:
        from_attributes = True
