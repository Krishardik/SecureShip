from datetime import datetime, timezone

import jwt

from app.core.config import settings
from app.services.token import ACCESS_TOKEN_TYPE, create_access_token


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def test_create_access_token_contains_user_id():
    payload = decode_access_token(create_access_token(user_id=123))
    assert payload["sub"] == "123"


def test_create_access_token_contains_expiration():
    payload = decode_access_token(create_access_token(user_id=123))
    assert "exp" in payload
    assert payload["exp"] > datetime.now(timezone.utc).timestamp()


def test_create_access_token_contains_issued_at():
    payload = decode_access_token(create_access_token(user_id=123))
    assert "iat" in payload
    assert payload["iat"] <= datetime.now(timezone.utc).timestamp()


def test_create_access_token_contains_access_token_type():
    payload = decode_access_token(create_access_token(user_id=123))
    assert payload["typ"] == ACCESS_TOKEN_TYPE
