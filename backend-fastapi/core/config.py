from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://labari:labari@localhost:5432/labari"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_days: int = 7
    aws_region: str = "us-east-1"
    images_bucket: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
