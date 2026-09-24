from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    api_port: int = 8000
    service_name: str = "exceptionlineage-api"
    version: str = "0.1.0"

    # Neo4j Graph Database
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
