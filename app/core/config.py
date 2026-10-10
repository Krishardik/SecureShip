from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "SecureShip"
    environment: str = "development"
    database_url: str = "sqlite:///./secureship.db"

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # Comma-separated values are read from environment variables.
    allowed_origins: list[str] = ["http://localhost:3000"]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver"]

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, value: str) -> str:
        if value.strip() != value:
            raise ValueError(
                "JWT_SECRET_KEY must not contain leading or trailing spaces"
            )

        if value.lower() in {
            "secret",
            "password",
            "change-me",
            "change-me-in-production",
            "development-only-secret-key-32-bytes-min",
        }:
            raise ValueError("JWT_SECRET_KEY must not use a known insecure value")

        return value

    @field_validator("allowed_origins", "allowed_hosts")
    @classmethod
    def validate_non_empty_entries(cls, values: list[str]) -> list[str]:
        normalized = [value.strip() for value in values if value.strip()]

        if not normalized:
            raise ValueError("Security allowlists must not be empty")

        return normalized


settings = Settings()
