from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User
from app.services.token import create_access_token


def create_test_user(db_session: Session) -> User:
    user = User(
        email="logging-user@example.com",
        password_hash=hash_password("StrongPassword123!"),
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_successful_login_is_logged(
    client: TestClient,
    db_session: Session,
    caplog,
):
    create_test_user(db_session)

    with caplog.at_level("INFO", logger="secureship.security"):
        response = client.post(
            "/users/login",
            json={
                "email": "logging-user@example.com",
                "password": "StrongPassword123!",
            },
        )

    assert response.status_code == 200

    messages = [record.getMessage() for record in caplog.records]

    assert "Authentication successful" in messages
    assert "StrongPassword123!" not in caplog.text
    assert "password_hash" not in caplog.text
    assert "access_token" not in caplog.text


def test_failed_login_is_logged_without_password(
    client: TestClient,
    db_session: Session,
    caplog,
):
    create_test_user(db_session)

    with caplog.at_level("WARNING", logger="secureship.security"):
        response = client.post(
            "/users/login",
            json={
                "email": "logging-user@example.com",
                "password": "WrongPassword123!",
            },
        )

    assert response.status_code == 401

    messages = [record.getMessage() for record in caplog.records]

    assert "Authentication failed: invalid password" in messages
    assert "WrongPassword123!" not in caplog.text
    assert "StrongPassword123!" not in caplog.text
    assert "password_hash" not in caplog.text


def test_invalid_token_is_logged_without_logging_token(
    client: TestClient,
    caplog,
):
    token = "not-a-real-secret-token"

    with caplog.at_level("WARNING", logger="secureship.security"):
        response = client.post(
            "/projects",
            json={"name": "SecureShip"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 401

    messages = [record.getMessage() for record in caplog.records]

    assert "Authentication failed: invalid or expired token" in messages
    assert token not in caplog.text


def test_successful_authenticated_request_does_not_log_token(
    client: TestClient,
    db_session: Session,
    caplog,
):
    user = create_test_user(db_session)
    token = create_access_token(user.id)

    with caplog.at_level("WARNING", logger="secureship.security"):
        response = client.get(
            "/projects/99999",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404
    assert token not in caplog.text
