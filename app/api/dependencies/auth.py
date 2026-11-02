import logging

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.services.token import ACCESS_TOKEN_TYPE

security_logger = logging.getLogger("secureship.security")

bearer_scheme = HTTPBearer()


def _unauthorized(detail: str = "Invalid or expired token") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> User:
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={
                "require": ["sub", "iat", "exp", "typ"],
                "verify_iat": True,
            },
        )
    except jwt.MissingRequiredClaimError as exc:
        security_logger.warning(
            "Authentication failed: required token claim missing",
            extra={"event": "token_validation_failure"},
        )
        detail = "Invalid token" if exc.claim == "sub" else "Invalid or expired token"
        raise _unauthorized(detail) from None
    except jwt.PyJWTError:
        security_logger.warning(
            "Authentication failed: invalid or expired token",
            extra={"event": "token_validation_failure"},
        )
        raise _unauthorized() from None

    user_id_claim = payload.get("sub")

    if not isinstance(user_id_claim, str) or not user_id_claim.isdecimal():
        security_logger.warning(
            "Authentication failed: invalid token subject",
            extra={"event": "token_validation_failure"},
        )
        raise _unauthorized("Invalid token") from None

    if payload.get("typ") != ACCESS_TOKEN_TYPE:
        security_logger.warning(
            "Authentication failed: incorrect token type",
            extra={"event": "token_validation_failure"},
        )
        raise _unauthorized("Invalid token") from None

    try:
        user_id = int(user_id_claim)
    except (TypeError, ValueError, OverflowError):
        security_logger.warning(
            "Authentication failed: invalid token subject",
            extra={"event": "token_validation_failure"},
        )
        raise _unauthorized("Invalid token") from None

    if user_id <= 0:
        security_logger.warning(
            "Authentication failed: invalid token subject",
            extra={"event": "token_validation_failure"},
        )
        raise _unauthorized("Invalid token") from None

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        security_logger.warning(
            "Authentication failed: token references unknown user",
            extra={
                "event": "token_validation_failure",
                "user_id": user_id,
            },
        )
        raise _unauthorized("User not found")

    if not user.is_active:
        security_logger.warning(
            "Authentication failed: inactive user",
            extra={
                "event": "inactive_user_authentication",
                "user_id": user.id,
            },
        )
        raise _unauthorized("Inactive user")

    return user
