import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server binding (Render passes PORT, local dev uses API_PORT or 8000)
    port: int | None = None
    api_port: int = 8000
    service_name: str = "exceptionlineage-api"
    version: str = "0.1.0"

    # CORS configuration for cross-domain Vercel frontend to Render backend
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    cors_origin_regex: str | None = r"^https://.*\.vercel\.app$"

    # Neo4j Graph Database (Supports local bolt:// and cloud Neo4j Aura neo4j+s://)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"
    neo4j_max_connection_lifetime: int = 200  # Seconds; prevents stale connections on cloud load balancers (Aura)
    neo4j_connection_timeout: float = 30.0

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}

    @property
    def effective_port(self) -> int:
        """Return runtime port, prioritizing cloud provider PORT over API_PORT."""
        if self.port is not None:
            return self.port
        env_port = os.getenv("PORT")
        if env_port:
            try:
                return int(env_port)
            except ValueError:
                pass
        return self.api_port

    @property
    def cors_origins_list(self) -> list[str]:
        """Return parsed list of allowed CORS origins."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

