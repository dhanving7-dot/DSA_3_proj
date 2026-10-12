from tests.conftest import register_and_login


def test_register_and_login(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "password": "secretpass1", "full_name": "Alice", "role": "STUDENT"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["email"] == "alice@example.com"
    assert body["access_token"]

    resp = client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "secretpass1"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_wrong_password_rejected(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "bob@example.com", "password": "secretpass1", "full_name": "Bob", "role": "STUDENT"},
    )
    resp = client.post("/api/v1/auth/login", json={"email": "bob@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_duplicate_registration_rejected(client):
    payload = {"email": "dup@example.com", "password": "secretpass1", "full_name": "Dup", "role": "STUDENT"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 400


def test_me_requires_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client):
    headers = register_and_login(client, email="carol@example.com")
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "carol@example.com"


def test_role_based_access_denied_for_student(client):
    headers = register_and_login(client, email="student@example.com", role="STUDENT")
    resp = client.post(
        "/api/v1/students",
        json={"roll_number": "R1", "full_name": "X", "email": "x@x.com", "department": "CSE", "year": 2},
        headers=headers,
    )
    assert resp.status_code == 403
