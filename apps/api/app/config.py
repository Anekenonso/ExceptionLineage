from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    api_port: int = 8000
    service_name: str = "exceptionlineage-api"
    version: str = "0.1.0"

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
