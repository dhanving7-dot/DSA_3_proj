from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.student import Student, StudentPreference
from app.models.user import User
from app.schemas.student import StudentPreferenceIn, StudentPreferenceOut

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=list[StudentPreferenceOut])
def list_preferences(student_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return (
        db.query(StudentPreference)
        .filter(StudentPreference.student_id == student_id)
        .order_by(StudentPreference.rank)
        .all()
    )


@router.post("", response_model=StudentPreferenceOut, status_code=status.HTTP_201_CREATED)
def add_preference(
    student_id: int, payload: StudentPreferenceIn, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    if not db.get(Student, student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    existing = db.query(StudentPreference).filter(StudentPreference.student_id == student_id).all()
    if any(p.rank == payload.rank for p in existing):
        raise HTTPException(status_code=400, detail="Rank already used by another preference")
    if any(p.lab_id == payload.lab_id for p in existing):
        raise HTTPException(status_code=400, detail="Laboratory already in preference list")
    pref = StudentPreference(student_id=student_id, **payload.model_dump())
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref


@router.delete("/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_preference(preference_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    pref = db.get(StudentPreference, preference_id)
    if not pref:
        raise HTTPException(status_code=404, detail="Preference not found")
    db.delete(pref)
    db.commit()
