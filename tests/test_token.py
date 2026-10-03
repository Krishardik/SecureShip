from datetime import datetime, timezone

import jwt

from app.core.config import settings
from app.services.token import create_access_token


def test_create_access_token_contains_user_id():
    token = create_access_token(user_id=123)

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == "123"


def test_create_access_token_contains_expiration():
    token = create_access_token(user_id=123)

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert "exp" in payload
    assert payload["exp"] > datetime.now(timezone.utc).timestamp()


def test_create_access_token_contains_issued_at():
    token = create_access_token(user_id=123)

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert "iat" in payload
    assert payload["iat"] <= datetime.now(timezone.utc).timestamp()
