from fastapi.testclient import TestClient


def test_registration_rejects_invalid_email(client: TestClient):
    response = client.post(
        "/users/register",
        json={
            "email": "not-an-email",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 422


def test_registration_rejects_short_password(client: TestClient):
    response = client.post(
        "/users/register",
        json={
            "email": "validation@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_registration_rejects_password_over_maximum_length(
    client: TestClient,
):
    response = client.post(
        "/users/register",
        json={
            "email": "long-password@example.com",
            "password": "A" * 129,
        },
    )

    assert response.status_code == 422


def test_registration_rejects_unexpected_fields(client: TestClient):
    response = client.post(
        "/users/register",
        json={
            "email": "extra-field@example.com",
            "password": "StrongPassword123!",
            "is_active": False,
        },
    )

    assert response.status_code == 422


def test_login_rejects_unexpected_fields(client: TestClient):
    response = client.post(
        "/users/login",
        json={
            "email": "login@example.com",
            "password": "StrongPassword123!",
            "is_admin": True,
        },
    )

    assert response.status_code == 422


def test_registration_rejects_missing_password(client: TestClient):
    response = client.post(
        "/users/register",
        json={"email": "missing-password@example.com"},
    )

    assert response.status_code == 422


def test_registration_rejects_malformed_json(client: TestClient):
    response = client.post(
        "/users/register",
        content='{"email": "broken@example.com",',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
