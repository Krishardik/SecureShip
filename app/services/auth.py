from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import User


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    normalized_email = email.lower()

    user = db.query(User).filter(User.email == normalized_email).first()

    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user
