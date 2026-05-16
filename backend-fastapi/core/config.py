from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://labari:labari@localhost:5432/labari"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_days: int = 7
    aws_region: str = "us-east-1"
    images_bucket: str = ""
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    environment: str = "development"

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_must_be_set(cls, v: str) -> str:
        if v == "change-me-in-production":
            raise ValueError(
                "JWT_SECRET must be set to a strong random value. "
                "Generate one with: openssl rand -hex 32"
            )
        return v

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
