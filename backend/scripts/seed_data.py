"""Seeds the database with realistic demo data: 220 students across 5
departments, 10 laboratories with varied capacity/equipment/skill
requirements, randomized skills and ranked preferences, plus one admin,
one faculty and a handful of student login accounts.

Run with:  python -m scripts.seed_data
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from faker import Faker  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.laboratory import LabEquipment, LabSkill, Laboratory, LabStatus, LabTimeSlot  # noqa: E402
from app.models.student import Student, StudentPreference, StudentSkill  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402

fake = Faker()
random.seed(2024)
Faker.seed(2024)

DEPARTMENTS = ["CSE", "ECE", "EEE", "MECH", "CIVIL", "IT", "AIML"]

DEPARTMENT_SKILLS = {
    "CSE": ["Python", "Java", "Data Structures", "Machine Learning", "Databases", "Operating Systems"],
    "ECE": ["Circuit Design", "Signal Processing", "Embedded C", "VLSI", "Communication Systems"],
    "EEE": ["Power Systems", "Control Systems", "Circuit Design", "MATLAB"],
    "MECH": ["CAD", "Thermodynamics", "Manufacturing", "SolidWorks"],
    "CIVIL": ["AutoCAD", "Structural Analysis", "Surveying", "Construction Management"],
    "IT": ["Python", "Networking", "Cloud Computing", "Databases", "Cybersecurity"],
    "AIML": ["Python", "Machine Learning", "Deep Learning", "Data Structures", "Statistics"],
}

LABS = [
    {
        "code": "AI-LAB-01",
        "name": "Artificial Intelligence Laboratory",
        "department": "AIML",
        "capacity": 30,
        "location": "Block A - Room 201",
        "skills": [("Machine Learning", 3), ("Python", 3)],
        "equipment": [("GPU Workstation", 20), ("NVIDIA DGX Node", 2)],
    },
    {
        "code": "DBMS-LAB-01",
        "name": "Database Management Systems Laboratory",
        "department": "CSE",
        "capacity": 35,
        "location": "Block A - Room 105",
        "skills": [("Databases", 2)],
        "equipment": [("Workstation", 35), ("SQL Server License", 35)],
    },
    {
        "code": "NET-LAB-01",
        "name": "Computer Networks Laboratory",
        "department": "IT",
        "capacity": 30,
        "location": "Block B - Room 210",
        "skills": [("Networking", 2)],
        "equipment": [("Router", 10), ("Switch", 15), ("Network Analyzer", 5)],
    },
    {
        "code": "OS-LAB-01",
        "name": "Operating Systems Laboratory",
        "department": "CSE",
        "capacity": 30,
        "location": "Block A - Room 110",
        "skills": [("Operating Systems", 2)],
        "equipment": [("Workstation", 30)],
    },
    {
        "code": "VLSI-LAB-01",
        "name": "VLSI Design Laboratory",
        "department": "ECE",
        "capacity": 25,
        "location": "Block C - Room 301",
        "skills": [("VLSI", 3)],
        "equipment": [("FPGA Board", 25), ("Oscilloscope", 10)],
    },
    {
        "code": "SIG-LAB-01",
        "name": "Signal Processing Laboratory",
        "department": "ECE",
        "capacity": 25,
        "location": "Block C - Room 305",
        "skills": [("Signal Processing", 2)],
        "equipment": [("DSP Kit", 25)],
    },
    {
        "code": "PWR-LAB-01",
        "name": "Power Systems Laboratory",
        "department": "EEE",
        "capacity": 25,
        "location": "Block D - Room 110",
        "skills": [("Power Systems", 2)],
        "equipment": [("Circuit Breaker Trainer", 10), ("MATLAB License", 25)],
    },
    {
        "code": "CAD-LAB-01",
        "name": "Computer Aided Design Laboratory",
        "department": "MECH",
        "capacity": 30,
        "location": "Block E - Room 201",
        "skills": [("CAD", 2)],
        "equipment": [("Workstation", 30), ("SolidWorks License", 30)],
    },
    {
        "code": "STRUCT-LAB-01",
        "name": "Structural Analysis Laboratory",
        "department": "CIVIL",
        "capacity": 25,
        "location": "Block F - Room 101",
        "skills": [("Structural Analysis", 2)],
        "equipment": [("Universal Testing Machine", 5), ("Compression Testing Machine", 3)],
    },
    {
        "code": "CLOUD-LAB-01",
        "name": "Cloud Computing Laboratory",
        "department": "IT",
        "capacity": 30,
        "location": "Block B - Room 220",
        "skills": [("Cloud Computing", 2), ("Python", 2)],
        "equipment": [("Workstation", 30), ("AWS Credits", 30)],
    },
]

TIME_SLOTS = [(0, "09:00", "11:00"), (1, "11:00", "13:00"), (2, "14:00", "16:00"), (3, "09:00", "11:00")]


def seed() -> None:
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(Student).count() > 0:
            print("Database already contains students; skipping seed to avoid duplicates.")
            return

        print("Creating accounts...")
        db.add(User(email="admin@campus.edu", hashed_password=hash_password("Admin@123"), full_name="System Administrator", role=UserRole.ADMIN))
        db.add(User(email="faculty@campus.edu", hashed_password=hash_password("Faculty@123"), full_name="Dr. Faculty Coordinator", role=UserRole.FACULTY))
        db.flush()

        print("Creating laboratories...")
        lab_objs: list[Laboratory] = []
        for lab_def in LABS:
            lab = Laboratory(
                code=lab_def["code"],
                name=lab_def["name"],
                department=lab_def["department"],
                capacity=lab_def["capacity"],
                location=lab_def["location"],
                status=LabStatus.ACTIVE,
            )
            db.add(lab)
            db.flush()
            for skill_name, min_prof in lab_def["skills"]:
                db.add(LabSkill(lab_id=lab.id, skill_name=skill_name, min_proficiency=min_prof, required=True))
            for equip_name, qty in lab_def["equipment"]:
                db.add(LabEquipment(lab_id=lab.id, equipment_name=equip_name, quantity=qty))
            for day, start, end in random.sample(TIME_SLOTS, k=2):
                db.add(LabTimeSlot(lab_id=lab.id, day_of_week=day, start_time=start, end_time=end, is_available=True))
            lab_objs.append(lab)
        db.flush()

        # one lab under maintenance to exercise the "unavailable laboratory" path
        maintenance_lab = Laboratory(
            code="MAINT-LAB-01", name="Robotics Laboratory (Under Maintenance)",
            department="MECH", capacity=20, location="Block E - Room 310", status=LabStatus.MAINTENANCE,
        )
        db.add(maintenance_lab)
        db.flush()
        lab_objs.append(maintenance_lab)

        print("Creating students...")
        num_students = 220
        for i in range(1, num_students + 1):
            department = random.choice(DEPARTMENTS)
            year = random.randint(1, 4)
            roll_number = f"{2021 + (4 - year)}{department}{i:04d}"
            student = Student(
                roll_number=roll_number,
                full_name=fake.name(),
                email=f"student{i}@campus.edu",
                department=department,
                year=year,
                cgpa=round(random.uniform(5.5, 9.8), 2),
                priority_score=round(random.uniform(0.0, 1.0), 2),
            )
            db.add(student)
            db.flush()

            skill_pool = DEPARTMENT_SKILLS[department]
            num_skills = random.randint(1, min(4, len(skill_pool)))
            for skill_name in random.sample(skill_pool, k=num_skills):
                db.add(StudentSkill(student_id=student.id, skill_name=skill_name, proficiency_level=random.randint(1, 5)))

            dept_labs = [lab for lab in lab_objs if lab.status == LabStatus.ACTIVE]
            same_dept = [lab for lab in dept_labs if lab.department == department]
            other_dept = [lab for lab in dept_labs if lab.department != department]
            candidate_labs = (same_dept + random.sample(other_dept, k=min(3, len(other_dept))))
            random.shuffle(candidate_labs)
            num_prefs = random.randint(1, min(3, len(candidate_labs))) if candidate_labs else 0
            for rank, lab in enumerate(candidate_labs[:num_prefs], start=1):
                db.add(StudentPreference(student_id=student.id, lab_id=lab.id, rank=rank))

            if i % 40 == 0:
                db.add(
                    User(
                        email=f"student{i}@campus.edu",
                        hashed_password=hash_password("Student@123"),
                        full_name=student.full_name,
                        role=UserRole.STUDENT,
                    )
                )

            if i % 25 == 0:
                db.flush()
                print(f"  ...{i}/{num_students} students created")

        db.commit()
        print(f"Seed complete: {num_students} students, {len(lab_objs)} laboratories.")
        print("Login with admin@campus.edu / Admin@123 or faculty@campus.edu / Faculty@123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
