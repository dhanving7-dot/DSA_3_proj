from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin_or_faculty
from app.models.laboratory import Laboratory, LabEquipment, LabSkill, LabStatus, LabTimeSlot
from app.models.user import User
from app.schemas.laboratory import (
    LabCreate,
    LabEquipmentIn,
    LabOut,
    LabSkillIn,
    LabTimeSlotIn,
    LabUpdate,
)
from app.services import audit_service

router = APIRouter(prefix="/labs", tags=["laboratories"])


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def _loaded_query(db: Session):
    return db.query(Laboratory).options(
        selectinload(Laboratory.required_skills),
        selectinload(Laboratory.equipment),
        selectinload(Laboratory.time_slots),
    )


@router.get("", response_model=list[LabOut])
def list_labs(
    department: str | None = None,
    status: LabStatus | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = _loaded_query(db)
    if department:
        query = query.filter(Laboratory.department == department)
    if status:
        query = query.filter(Laboratory.status == status)
    return query.order_by(Laboratory.id).all()


@router.get("/{lab_id}", response_model=LabOut)
def get_lab(lab_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    lab = _loaded_query(db).filter(Laboratory.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    return lab


@router.post("", response_model=LabOut, status_code=status.HTTP_201_CREATED)
def create_lab(
    payload: LabCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty),
):
    if db.query(Laboratory).filter(Laboratory.code == payload.code).first():
        raise HTTPException(status_code=400, detail="Laboratory code already exists")

    lab = Laboratory(**payload.model_dump(exclude={"required_skills", "equipment", "time_slots"}))
    db.add(lab)
    db.flush()

    for skill in payload.required_skills:
        db.add(LabSkill(lab_id=lab.id, **skill.model_dump()))
    for equip in payload.equipment:
        db.add(LabEquipment(lab_id=lab.id, **equip.model_dump()))
    for slot in payload.time_slots:
        db.add(LabTimeSlot(lab_id=lab.id, **slot.model_dump()))

    db.commit()
    db.refresh(lab)
    audit_service.log_action(db, current_user.id, "CREATE", "Laboratory", str(lab.id), {}, _client_ip(request))
    return lab


@router.put("/{lab_id}", response_model=LabOut)
def update_lab(
    lab_id: int,
    payload: LabUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty),
):
    lab = db.get(Laboratory, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lab, field, value)
    db.commit()
    db.refresh(lab)
    audit_service.log_action(db, current_user.id, "UPDATE", "Laboratory", str(lab.id), {}, _client_ip(request))
    return lab


@router.delete("/{lab_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lab(
    lab_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty),
):
    lab = db.get(Laboratory, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    db.delete(lab)
    db.commit()
    audit_service.log_action(db, current_user.id, "DELETE", "Laboratory", str(lab_id), {}, _client_ip(request))


@router.post("/{lab_id}/skills", response_model=LabOut, status_code=status.HTTP_201_CREATED)
def add_required_skill(
    lab_id: int, payload: LabSkillIn, db: Session = Depends(get_db), _: User = Depends(require_admin_or_faculty)
):
    lab = db.get(Laboratory, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    db.add(LabSkill(lab_id=lab_id, **payload.model_dump()))
    db.commit()
    db.refresh(lab)
    return lab


@router.post("/{lab_id}/equipment", response_model=LabOut, status_code=status.HTTP_201_CREATED)
def add_equipment(
    lab_id: int, payload: LabEquipmentIn, db: Session = Depends(get_db), _: User = Depends(require_admin_or_faculty)
):
    lab = db.get(Laboratory, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    db.add(LabEquipment(lab_id=lab_id, **payload.model_dump()))
    db.commit()
    db.refresh(lab)
    return lab


@router.post("/{lab_id}/time-slots", response_model=LabOut, status_code=status.HTTP_201_CREATED)
def add_time_slot(
    lab_id: int, payload: LabTimeSlotIn, db: Session = Depends(get_db), _: User = Depends(require_admin_or_faculty)
):
    lab = db.get(Laboratory, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found")
    db.add(LabTimeSlot(lab_id=lab_id, **payload.model_dump()))
    db.commit()
    db.refresh(lab)
    return lab
