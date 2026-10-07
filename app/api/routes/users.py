import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.models import User
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth import authenticate_user
from app.services.token import create_access_token

security_logger = logging.getLogger("secureship.security")

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),  # noqa: B008
):
    normalized_email = str(user.email).lower()

    existing_user = db.query(User).filter(User.email == normalized_email).first()

    if existing_user:
        security_logger.warning(
            "Registration failed: email already registered",
            extra={"event": "registration_failure"},
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    password_hash = hash_password(user.password)

    new_user = User(
        email=normalized_email,
        password_hash=password_hash,
    )

    db.add(new_user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        security_logger.warning(
            "Registration failed: duplicate email",
            extra={"event": "registration_failure"},
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from None

    db.refresh(new_user)

    security_logger.info(
        "User registration successful",
        extra={
            "event": "registration_success",
            "user_id": new_user.id,
        },
    )

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db),  # noqa: B008
):
    authenticated_user = authenticate_user(
        db,
        user.email,
        user.password,
    )

    if authenticated_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(authenticated_user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
