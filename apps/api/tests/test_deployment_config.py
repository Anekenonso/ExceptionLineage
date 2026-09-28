"""Tests for deployment configuration, CORS settings, and production port bindings."""

import os
import re
from unittest.mock import patch

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app


def test_settings_port_resolution():
    """effective_port prioritizes PORT over API_PORT."""
    # When explicit port is set
    s1 = Settings(port=9000, api_port=8000)
    assert s1.effective_port == 9000

    # When port is None but PORT environment variable is set
    with patch.dict(os.environ, {"PORT": "10000"}):
        s2 = Settings(port=None, api_port=8000)
        assert s2.effective_port == 10000

    # When no PORT env var is present, falls back to api_port
    with patch.dict(os.environ, {}, clear=True):
        s3 = Settings(port=None, api_port=8080)
        assert s3.effective_port == 8080


def test_settings_cors_origins_parsing():
    """cors_origins_list correctly parses comma-separated strings."""
    s = Settings(cors_origins="https://app.vercel.app, http://localhost:3000 , https://custom.domain.com")
    origins = s.cors_origins_list
    assert origins == [
        "https://app.vercel.app",
        "http://localhost:3000",
        "https://custom.domain.com",
    ]


def test_settings_cors_origin_regex():
    """cors_origin_regex matches Vercel domains and preview branches."""
    s = Settings(cors_origin_regex=r"^https://.*\.vercel\.app$")
    assert re.match(s.cors_origin_regex, "https://exceptionlineage.vercel.app")
    assert re.match(s.cors_origin_regex, "https://exceptionlineage-git-preview.vercel.app")
    assert not re.match(s.cors_origin_regex, "http://malicious.site.com")


def test_cors_middleware_allows_cross_origin_requests():
    """FastAPI app allows preflight OPTIONS request from configured origin without credentials."""
    client = TestClient(app)
    response = client.options(
        "/api/investigations",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") is None


def test_cors_credentials_hardened_to_false():
    """FastAPI CORS policy strictly disallows credentialed requests."""
    client = TestClient(app)
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") is None


def test_neo4j_aura_connection_settings():
    """Neo4j settings include connection timeout and cloud lifetime values."""
    s = Settings(
        neo4j_uri="neo4j+s://xyz.databases.neo4j.io",
        neo4j_max_connection_lifetime=200,
        neo4j_connection_timeout=45.0,
    )
    assert s.neo4j_uri.startswith("neo4j+s://")
    assert s.neo4j_max_connection_lifetime == 200
    assert s.neo4j_connection_timeout == 45.0
