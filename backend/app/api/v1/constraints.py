from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.constraint import Constraint
from app.models.user import User
from app.schemas.constraint import ConstraintCreate, ConstraintOut, ConstraintUpdate

router = APIRouter(prefix="/constraints", tags=["constraints"])


@router.get("", response_model=list[ConstraintOut])
def list_constraints(active_only: bool = False, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    query = db.query(Constraint)
    if active_only:
        query = query.filter(Constraint.is_active.is_(True))
    return query.order_by(Constraint.id).all()


@router.post("", response_model=ConstraintOut, status_code=status.HTTP_201_CREATED)
def create_constraint(payload: ConstraintCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    constraint = Constraint(**payload.model_dump())
    db.add(constraint)
    db.commit()
    db.refresh(constraint)
    return constraint


@router.put("/{constraint_id}", response_model=ConstraintOut)
def update_constraint(
    constraint_id: int, payload: ConstraintUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    constraint = db.get(Constraint, constraint_id)
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(constraint, field, value)
    db.commit()
    db.refresh(constraint)
    return constraint


@router.delete("/{constraint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_constraint(constraint_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    constraint = db.get(Constraint, constraint_id)
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint not found")
    db.delete(constraint)
    db.commit()
