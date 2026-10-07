import logging

from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import User

security_logger = logging.getLogger("secureship.security")


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    normalized_email = email.lower()

    user = db.query(User).filter(User.email == normalized_email).first()

    if user is None:
        security_logger.warning(
            "Authentication failed: unknown user",
            extra={"event": "authentication_failure"},
        )
        return None

    if not verify_password(password, user.password_hash):
        security_logger.warning(
            "Authentication failed: invalid password",
            extra={
                "event": "authentication_failure",
                "user_id": user.id,
            },
        )
        return None

    security_logger.info(
        "Authentication successful",
        extra={
            "event": "authentication_success",
            "user_id": user.id,
        },
    )

    return user
