from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "SecureShip"
    environment: str = "development"


settings = Settings()
