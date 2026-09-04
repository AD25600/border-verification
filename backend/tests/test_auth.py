def _register_officer(client, email="officer.test@demo.example"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Test Officer",
            "password": "TestPass@123",
            "role_name": "OFFICER",
        },
    )


def test_register_user(client):
    response = _register_officer(client)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "officer.test@demo.example"
    assert "password" not in body
    assert "hashed_password" not in body


def test_login_success(client):
    _register_officer(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "officer.test@demo.example", "password": "TestPass@123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid_password(client):
    _register_officer(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "officer.test@demo.example", "password": "WrongPassword"},
    )
    assert response.status_code == 401


def test_protected_endpoint_requires_auth(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_protected_endpoint_with_token(client):
    _register_officer(client)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "officer.test@demo.example", "password": "TestPass@123"},
    )
    token = login.json()["access_token"]
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "officer.test@demo.example"


def test_role_protection_blocks_officer_from_admin_route(client):
    _register_officer(client, email="officer2@demo.example")
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "officer2@demo.example", "password": "TestPass@123"},
    )
    token = login.json()["access_token"]
    response = client.post(
        "/api/v1/checkpoints",
        json={"name": "Test Checkpoint", "code": "TST-01", "location": "Nowhere"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
