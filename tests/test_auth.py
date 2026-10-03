from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User
from app.services.auth import authenticate_user


def test_authenticate_user_returns_user_for_valid_credentials(
    db_session: Session,
):
    password = "StrongPassword123!"

    user = User(
        email="auth@example.com",
        password_hash=hash_password(password),
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    authenticated_user = authenticate_user(
        db_session,
        "auth@example.com",
        password,
    )

    assert authenticated_user is not None
    assert authenticated_user.id == user.id


def test_authenticate_user_rejects_wrong_password(
    db_session: Session,
):
    user = User(
        email="wrong-password@example.com",
        password_hash=hash_password("StrongPassword123!"),
    )

    db_session.add(user)
    db_session.commit()

    authenticated_user = authenticate_user(
        db_session,
        "wrong-password@example.com",
        "WrongPassword123!",
    )

    assert authenticated_user is None


def test_authenticate_user_rejects_unknown_email(
    db_session: Session,
):
    authenticated_user = authenticate_user(
        db_session,
        "unknown@example.com",
        "StrongPassword123!",
    )

    assert authenticated_user is None
