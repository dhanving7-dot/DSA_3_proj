import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin_or_faculty
from app.models.student import Student, StudentPreference, StudentSkill
from app.models.user import User
from app.schemas.student import (
    StudentCreate,
    StudentOut,
    StudentPreferenceIn,
    StudentSkillIn,
    StudentUpdate,
)
from app.services import audit_service

router = APIRouter(prefix="/students", tags=["students"])


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


@router.get("", response_model=list[StudentOut])
def list_students(
    department: str | None = None,
    year: int | None = None,
    search: str | None = Query(default=None, description="Matches roll number, name or email"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Student).options(selectinload(Student.skills), selectinload(Student.preferences))
    if department:
        query = query.filter(Student.department == department)
    if year:
        query = query.filter(Student.year == year)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Student.roll_number.ilike(like)) | (Student.full_name.ilike(like)) | (Student.email.ilike(like))
        )
    return query.order_by(Student.id).offset(skip).limit(limit).all()


@router.get("/export")
def export_students(db: Session = Depends(get_db), _: User = Depends(require_admin_or_faculty)):
    students = db.query(Student).options(selectinload(Student.skills), selectinload(Student.preferences)).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["roll_number", "full_name", "email", "department", "year", "cgpa", "priority_score", "skills", "preferences"])
    for s in students:
        skills = ";".join(f"{sk.skill_name}:{sk.proficiency_level}" for sk in s.skills)
        prefs = ";".join(f"{p.lab_id}:{p.rank}" for p in s.preferences)
        writer.writerow([s.roll_number, s.full_name, s.email, s.department, s.year, s.cgpa, s.priority_score, skills, prefs])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students_export.csv"},
    )


@router.post("/import", status_code=status.HTTP_201_CREATED)
async def import_students(
    file: UploadFile,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty),
):
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    created = 0
    errors: list[str] = []
    for i, row in enumerate(reader, start=2):
        try:
            roll_number = row["roll_number"].strip()
            if db.query(Student).filter(Student.roll_number == roll_number).first():
                errors.append(f"Row {i}: roll_number {roll_number} already exists, skipped")
                continue
            student = Student(
                roll_number=roll_number,
                full_name=row["full_name"].strip(),
                email=row["email"].strip(),
                department=row["department"].strip(),
                year=int(row["year"]),
                cgpa=float(row.get("cgpa") or 0),
                priority_score=float(row.get("priority_score") or 0),
            )
            db.add(student)
            db.flush()
            skills_raw = row.get("skills") or ""
            for chunk in filter(None, skills_raw.split(";")):
                name, _, level = chunk.partition(":")
                db.add(StudentSkill(student_id=student.id, skill_name=name.strip(), proficiency_level=int(level or 1)))
            created += 1
        except Exception as exc:  # noqa: BLE001 - surfaced to caller as a row-level import error
            errors.append(f"Row {i}: {exc}")
    db.commit()

    audit_service.log_action(
        db, current_user.id, "CSV_IMPORT", "Student", "", {"created": created, "errors": len(errors)}, _client_ip(request)
    )
    return {"created": created, "errors": errors}


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty),
):
    if db.query(Student).filter(Student.roll_number == payload.roll_number).first():
        raise HTTPException(status_code=400, detail="roll_number already exists")

    student = Student(**payload.model_dump(exclude={"skills", "preferences"}))
    db.add(student)
    db.flush()

    for skill in payload.skills:
        db.add(StudentSkill(student_id=student.id, **skill.model_dump()))
    for pref in payload.preferences:
        db.add(StudentPreference(student_id=student.id, **pref.model_dump()))

    db.commit()
    db.refresh(student)

    audit_service.log_action(db, current_user.id, "CREATE", "Student", str(student.id), {}, _client_ip(request))
    return student


@router.put("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    audit_service.log_action(db, current_user.id, "UPDATE", "Student", str(student.id), {}, _client_ip(request))
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    audit_service.log_action(db, current_user.id, "DELETE", "Student", str(student_id), {}, _client_ip(request))


@router.post("/{student_id}/skills", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def add_skill(
    student_id: int,
    payload: StudentSkillIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if any(sk.skill_name == payload.skill_name for sk in student.skills):
        raise HTTPException(status_code=400, detail="Skill already recorded for this student")
    db.add(StudentSkill(student_id=student_id, **payload.model_dump()))
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}/skills/{skill_id}", response_model=StudentOut)
def remove_skill(
    student_id: int,
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_faculty),
):
    skill = db.get(StudentSkill, skill_id)
    if not skill or skill.student_id != student_id:
        raise HTTPException(status_code=404, detail="Skill not found")
    db.delete(skill)
    db.commit()
    student = db.get(Student, student_id)
    db.refresh(student)
    return student


@router.put("/{student_id}/preferences", response_model=StudentOut)
def set_preferences(
    student_id: int,
    payload: list[StudentPreferenceIn],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    ranks = [p.rank for p in payload]
    lab_ids = [p.lab_id for p in payload]
    if len(ranks) != len(set(ranks)):
        raise HTTPException(status_code=400, detail="Duplicate preference ranks are not allowed")
    if len(lab_ids) != len(set(lab_ids)):
        raise HTTPException(status_code=400, detail="Duplicate laboratory preferences are not allowed")

    db.query(StudentPreference).filter(StudentPreference.student_id == student_id).delete()
    db.flush()
    for pref in payload:
        db.add(StudentPreference(student_id=student_id, **pref.model_dump()))
    db.commit()
    db.refresh(student)
    return student
