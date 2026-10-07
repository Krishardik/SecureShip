import logging

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import User

security_logger = logging.getLogger("secureship.security")

bearer_scheme = HTTPBearer()


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
        )
    except jwt.PyJWTError:
        security_logger.warning(
            "Authentication failed: invalid or expired token",
            extra={"event": "token_validation_failure"},
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user_id = payload.get("sub")

    if user_id is None:
        security_logger.warning(
            "Authentication failed: token missing subject",
            extra={"event": "token_validation_failure"},
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        security_logger.warning(
            "Authentication failed: invalid token subject",
            extra={"event": "token_validation_failure"},
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        security_logger.warning(
            "Authentication failed: token references unknown user",
            extra={
                "event": "token_validation_failure",
                "user_id": user_id,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        security_logger.warning(
            "Authentication failed: inactive user",
            extra={
                "event": "inactive_user_authentication",
                "user_id": user.id,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
