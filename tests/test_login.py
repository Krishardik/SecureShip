from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User


def test_login_with_valid_credentials(
    client: TestClient,
    db_session: Session,
):
    password = "StrongPassword123!"

    user = User(
        email="login@example.com",
        password_hash=hash_password(password),
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.post(
        "/users/login",
        json={
            "email": "login@example.com",
            "password": password,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Authentication successful",
        "user_id": user.id,
    }


def test_login_rejects_wrong_password(
    client: TestClient,
    db_session: Session,
):
    user = User(
        email="wrong-password@example.com",
        password_hash=hash_password("StrongPassword123!"),
    )

    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/users/login",
        json={
            "email": "wrong-password@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password",
    }


def test_login_rejects_unknown_email(client: TestClient):
    response = client.post(
        "/users/login",
        json={
            "email": "unknown@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password",
    }
