import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_accepts_secure_jwt_secret():
    settings = Settings(
        jwt_secret_key="a" * 64,
    )

    assert settings.jwt_secret_key == "a" * 64


def test_settings_rejects_short_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(
            jwt_secret_key="too-short",
        )


def test_settings_rejects_known_insecure_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(
            jwt_secret_key="change-me",
        )


def test_settings_rejects_jwt_secret_with_surrounding_spaces():
    with pytest.raises(ValidationError):
        Settings(
            jwt_secret_key=" " + ("a" * 64),
        )


def test_settings_keeps_default_application_configuration():
    settings = Settings(
        jwt_secret_key="a" * 64,
    )

    assert settings.app_name == "SecureShip"
    assert settings.environment == "development"
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_access_token_expire_minutes == 30
