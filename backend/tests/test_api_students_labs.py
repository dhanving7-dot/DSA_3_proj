from tests.conftest import register_and_login


def create_lab(client, headers, code="LAB1", capacity=2, department="CSE"):
    return client.post(
        "/api/v1/labs",
        json={"code": code, "name": f"{code} Laboratory", "department": department, "capacity": capacity},
        headers=headers,
    )


def create_student(client, headers, roll="R001", department="CSE", year=2):
    return client.post(
        "/api/v1/students",
        json={
            "roll_number": roll,
            "full_name": "Student " + roll,
            "email": f"{roll.lower()}@example.com",
            "department": department,
            "year": year,
            "cgpa": 8.5,
        },
        headers=headers,
    )


def test_create_and_get_student(client):
    headers = register_and_login(client)
    resp = create_student(client, headers)
    assert resp.status_code == 201
    student_id = resp.json()["id"]

    resp = client.get(f"/api/v1/students/{student_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["roll_number"] == "R001"


def test_duplicate_roll_number_rejected(client):
    headers = register_and_login(client)
    create_student(client, headers, roll="R002")
    resp = create_student(client, headers, roll="R002")
    assert resp.status_code == 400


def test_update_and_delete_student(client):
    headers = register_and_login(client)
    student_id = create_student(client, headers, roll="R003").json()["id"]

    resp = client.put(f"/api/v1/students/{student_id}", json={"cgpa": 9.1}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["cgpa"] == 9.1

    resp = client.delete(f"/api/v1/students/{student_id}", headers=headers)
    assert resp.status_code == 204
    assert client.get(f"/api/v1/students/{student_id}", headers=headers).status_code == 404


def test_search_and_filter_students(client):
    headers = register_and_login(client)
    create_student(client, headers, roll="R004", department="CSE")
    create_student(client, headers, roll="R005", department="ECE")

    resp = client.get("/api/v1/students", params={"department": "ECE"}, headers=headers)
    assert resp.status_code == 200
    assert all(s["department"] == "ECE" for s in resp.json())

    resp = client.get("/api/v1/students", params={"search": "R004"}, headers=headers)
    assert len(resp.json()) == 1


def test_student_skill_management(client):
    headers = register_and_login(client)
    student_id = create_student(client, headers, roll="R006").json()["id"]

    resp = client.post(
        f"/api/v1/students/{student_id}/skills",
        json={"skill_name": "Python", "proficiency_level": 4},
        headers=headers,
    )
    assert resp.status_code == 201
    assert len(resp.json()["skills"]) == 1

    skill_id = resp.json()["skills"][0]["id"]
    resp = client.delete(f"/api/v1/students/{student_id}/skills/{skill_id}", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["skills"]) == 0


def test_student_preferences_reject_duplicates(client):
    headers = register_and_login(client)
    student_id = create_student(client, headers, roll="R007").json()["id"]
    lab_id = create_lab(client, headers, code="LABX").json()["id"]

    resp = client.put(
        f"/api/v1/students/{student_id}/preferences",
        json=[{"lab_id": lab_id, "rank": 1}, {"lab_id": lab_id, "rank": 2}],
        headers=headers,
    )
    assert resp.status_code == 400


def test_csv_export_and_import_round_trip(client):
    headers = register_and_login(client)
    create_student(client, headers, roll="R008")

    resp = client.get("/api/v1/students/export", headers=headers)
    assert resp.status_code == 200
    csv_text = resp.text
    assert "R008" in csv_text

    new_csv = "roll_number,full_name,email,department,year,cgpa,priority_score,skills,preferences\nR009,New Student,r009@x.com,CSE,3,7.5,0.2,Python:3,\n"
    files = {"file": ("students.csv", new_csv, "text/csv")}
    resp = client.post("/api/v1/students/import", files=files, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["created"] == 1


def test_create_lab_with_requirements(client):
    headers = register_and_login(client)
    resp = client.post(
        "/api/v1/labs",
        json={
            "code": "AI-LAB",
            "name": "AI Laboratory",
            "department": "CSE",
            "capacity": 30,
            "required_skills": [{"skill_name": "Machine Learning", "min_proficiency": 3, "required": True}],
            "equipment": [{"equipment_name": "GPU Workstation", "quantity": 10}],
            "time_slots": [{"day_of_week": 0, "start_time": "09:00", "end_time": "11:00", "is_available": True}],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["capacity"] == 30
    assert len(body["required_skills"]) == 1
    assert len(body["equipment"]) == 1
    assert len(body["time_slots"]) == 1


def test_duplicate_lab_code_rejected(client):
    headers = register_and_login(client)
    create_lab(client, headers, code="DUPLAB")
    resp = create_lab(client, headers, code="DUPLAB")
    assert resp.status_code == 400
