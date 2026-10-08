import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import login_rate_limiter
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

    data = response.json()

    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)

    payload = jwt.decode(
        data["access_token"],
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == str(user.id)


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


def test_login_rate_limit_blocks_after_five_failures(
    client: TestClient,
    db_session: Session,
):
    login_rate_limiter.clear()

    user = User(
        email="rate-limit@example.com",
        password_hash=hash_password("StrongPassword123!"),
    )

    db_session.add(user)
    db_session.commit()

    for _ in range(5):
        response = client.post(
            "/users/login",
            json={
                "email": "rate-limit@example.com",
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401

    response = client.post(
        "/users/login",
        json={
            "email": "rate-limit@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 429
    assert response.json() == {
        "detail": "Too many login attempts. Try again later.",
    }
    assert response.headers["Retry-After"] == "60"

    login_rate_limiter.clear()


def test_successful_login_resets_rate_limit(
    client: TestClient,
    db_session: Session,
):
    login_rate_limiter.clear()

    password = "StrongPassword123!"

    user = User(
        email="reset-rate-limit@example.com",
        password_hash=hash_password(password),
    )

    db_session.add(user)
    db_session.commit()

    for _ in range(4):
        response = client.post(
            "/users/login",
            json={
                "email": "reset-rate-limit@example.com",
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401

    response = client.post(
        "/users/login",
        json={
            "email": "reset-rate-limit@example.com",
            "password": password,
        },
    )

    assert response.status_code == 200

    response = client.post(
        "/users/login",
        json={
            "email": "reset-rate-limit@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401

    login_rate_limiter.clear()
