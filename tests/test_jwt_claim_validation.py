from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models import User
from app.services.token import create_access_token


def encode_token(payload: dict) -> str:
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def valid_payload(user_id: int) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "typ": "access",
    }


def create_test_user(db_session, email: str) -> User:
    user = User(
        email=email,
        password_hash="not-used-in-this-test",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_protected_endpoint_accepts_valid_access_token(
    client: TestClient,
    db_session,
):
    user = create_test_user(db_session, "jwt-valid@example.com")
    token = create_access_token(user.id)

    response = client.get(
        "/projects",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200


@pytest.mark.parametrize("missing_claim", ["sub", "iat", "exp", "typ"])
def test_protected_endpoint_rejects_missing_required_claims(
    client: TestClient,
    db_session,
    missing_claim: str,
):
    user = create_test_user(
        db_session,
        f"jwt-missing-{missing_claim}@example.com",
    )
    payload = valid_payload(user.id)
    payload.pop(missing_claim)

    response = client.get(
        "/projects",
        headers={"Authorization": f"Bearer {encode_token(payload)}"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "token_type",
    ["refresh", "password_reset", "unknown", "", None],
)
def test_protected_endpoint_rejects_non_access_token_types(
    client: TestClient,
    db_session,
    token_type: str | None,
):
    user = create_test_user(
        db_session,
        f"jwt-type-{token_type!s}@example.com",
    )
    payload = valid_payload(user.id)
    payload["typ"] = token_type

    response = client.get(
        "/projects",
        headers={"Authorization": f"Bearer {encode_token(payload)}"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "subject",
    ["", "0", "-1", "abc", "1.5", 123, None],
)
def test_protected_endpoint_rejects_invalid_subjects(
    client: TestClient,
    db_session,
    subject,
):
    user = create_test_user(
        db_session,
        f"jwt-subject-{subject!s}@example.com",
    )
    payload = valid_payload(user.id)
    payload["sub"] = subject

    response = client.get(
        "/projects",
        headers={"Authorization": f"Bearer {encode_token(payload)}"},
    )

    assert response.status_code == 401


def test_protected_endpoint_rejects_future_issued_token(
    client: TestClient,
    db_session,
):
    user = create_test_user(db_session, "jwt-future-iat@example.com")
    payload = valid_payload(user.id)
    payload["iat"] = datetime.now(timezone.utc) + timedelta(minutes=10)

    response = client.get(
        "/projects",
        headers={"Authorization": f"Bearer {encode_token(payload)}"},
    )

    assert response.status_code == 401
