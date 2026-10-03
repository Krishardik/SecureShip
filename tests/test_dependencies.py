from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.config import settings
from app.core.security import hash_password
from app.models import User


def test_get_current_user_returns_user(
    db_session: Session,
):
    user = User(
        email="current@example.com",
        password_hash=hash_password("StrongPassword123!"),
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = jwt.encode(
        {"sub": str(user.id)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    current_user = get_current_user(
        credentials=credentials,
        db=db_session,
    )

    assert current_user.id == user.id


def test_get_current_user_rejects_invalid_token(
    db_session: Session,
):
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="not-a-valid-jwt",
    )

    try:
        get_current_user(
            credentials=credentials,
            db=db_session,
        )
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Invalid or expired token"


def test_get_current_user_rejects_wrong_signature(
    db_session: Session,
):
    token = jwt.encode(
        {"sub": "1"},
        "this-is-a-different-secret-key-32",
        algorithm=settings.jwt_algorithm,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    try:
        get_current_user(
            credentials=credentials,
            db=db_session,
        )
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Invalid or expired token"


def test_get_current_user_rejects_expired_token(
    db_session: Session,
):
    token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    try:
        get_current_user(
            credentials=credentials,
            db=db_session,
        )
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Invalid or expired token"


def test_get_current_user_rejects_token_without_subject(
    db_session: Session,
):
    token = jwt.encode(
        {},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    try:
        get_current_user(
            credentials=credentials,
            db=db_session,
        )
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Invalid token"


def test_get_current_user_rejects_nonexistent_user(
    db_session: Session,
):
    token = jwt.encode(
        {"sub": "999999"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    try:
        get_current_user(
            credentials=credentials,
            db=db_session,
        )
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "User not found"


def test_get_current_user_rejects_inactive_user(
    db_session: Session,
):
    user = User(
        email="inactive@example.com",
        password_hash=hash_password("StrongPassword123!"),
        is_active=False,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = jwt.encode(
        {"sub": str(user.id)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    try:
        get_current_user(
            credentials=credentials,
            db=db_session,
        )
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 401
        assert exc.detail == "Inactive user"
