from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import User


def test_register_user(client: TestClient):
    response = client.post(
        "/users/register",
        json={
            "email": "user@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "user@example.com"
    assert data["is_active"] is True
    assert isinstance(data["id"], int)
    assert "password" not in data
    assert "password_hash" not in data


def test_register_user_hashes_password(client: TestClient):
    password = "StrongPassword123!"

    response = client.post(
        "/users/register",
        json={
            "email": "hash@example.com",
            "password": password,
        },
    )

    assert response.status_code == 201

    # The API response must not expose the password or its hash.
    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_register_user_rejects_duplicate_email(client: TestClient):
    payload = {
        "email": "duplicate@example.com",
        "password": "StrongPassword123!",
    }

    first_response = client.post("/users/register", json=payload)
    second_response = client.post("/users/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "Email is already registered"}


def test_register_user_rejects_invalid_email(client: TestClient):
    response = client.post(
        "/users/register",
        json={
            "email": "not-an-email",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 422


def test_register_user_rejects_short_password(client: TestClient):
    response = client.post(
        "/users/register",
        json={
            "email": "short@example.com",
            "password": "Short123!",
        },
    )

    assert response.status_code == 422


def test_register_user_stores_hashed_password(
    client: TestClient,
    db_session: Session,
):
    password = "StrongPassword123!"

    response = client.post(
        "/users/register",
        json={
            "email": "database@example.com",
            "password": password,
        },
    )

    assert response.status_code == 201

    user = db_session.query(User).filter(User.email == "database@example.com").first()

    assert user is not None
    assert user.password_hash != password
    assert user.password_hash.startswith("$argon2id$")
    assert verify_password(password, user.password_hash)


def test_register_user_normalizes_email(client: TestClient):
    response = client.post(
        "/users/register",
        json={
            "email": "User@Example.COM",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"
