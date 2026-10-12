from datetime import datetime

from pydantic import BaseModel, Field

from app.models.laboratory import LabStatus


class LabSkillIn(BaseModel):
    skill_name: str
    min_proficiency: int = Field(ge=1, le=5, default=1)
    required: bool = True


class LabSkillOut(LabSkillIn):
    id: int

    class Config:
        from_attributes = True


class LabEquipmentIn(BaseModel):
    equipment_name: str
    quantity: int = Field(ge=0, default=1)


class LabEquipmentOut(LabEquipmentIn):
    id: int

    class Config:
        from_attributes = True


class LabTimeSlotIn(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: str
    end_time: str
    is_available: bool = True


class LabTimeSlotOut(LabTimeSlotIn):
    id: int

    class Config:
        from_attributes = True


class LabBase(BaseModel):
    code: str
    name: str
    department: str
    capacity: int = Field(ge=0)
    location: str = ""
    status: LabStatus = LabStatus.ACTIVE


class LabCreate(LabBase):
    required_skills: list[LabSkillIn] = []
    equipment: list[LabEquipmentIn] = []
    time_slots: list[LabTimeSlotIn] = []


class LabUpdate(BaseModel):
    name: str | None = None
    department: str | None = None
    capacity: int | None = Field(default=None, ge=0)
    location: str | None = None
    status: LabStatus | None = None


class LabOut(LabBase):
    id: int
    created_at: datetime
    required_skills: list[LabSkillOut] = []
    equipment: list[LabEquipmentOut] = []
    time_slots: list[LabTimeSlotOut] = []

    class Config:
        from_attributes = True
