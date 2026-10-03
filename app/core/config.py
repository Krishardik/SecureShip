from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "SecureShip"
    environment: str = "development"
    database_url: str = "sqlite:///./secureship.db"

    jwt_secret_key: str = "development-only-secret-key-32-bytes-min"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30


settings = Settings()
