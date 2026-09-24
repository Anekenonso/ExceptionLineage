"""Tests for Neo4jClient connection handling, settings, and graceful degradation."""

from unittest.mock import MagicMock, patch

from neo4j.exceptions import ServiceUnavailable

from app.config import settings
from app.graph.client import Neo4jClient


def test_neo4j_client_initialization_defaults() -> None:
    client = Neo4jClient()
    assert client.uri == settings.neo4j_uri
    assert client.username == settings.neo4j_username
    assert client.password == settings.neo4j_password
    assert client.database == settings.neo4j_database


def test_neo4j_client_custom_config() -> None:
    client = Neo4jClient(
        uri="bolt://custom:7687",
        username="admin",
        password="secretpassword",
        database="custom_db",
    )
    assert client.uri == "bolt://custom:7687"
    assert client.username == "admin"
    assert client.password == "secretpassword"
    assert client.database == "custom_db"


def test_neo4j_client_verify_connectivity_returns_false_when_unreachable() -> None:
    mock_driver = MagicMock()
    mock_driver.verify_connectivity.side_effect = ServiceUnavailable("Failed to connect")

    client = Neo4jClient(driver=mock_driver)
    assert client.verify_connectivity() is False


def test_neo4j_client_verify_connectivity_returns_true_when_healthy() -> None:
    mock_driver = MagicMock()
    mock_driver.verify_connectivity.return_value = None

    client = Neo4jClient(driver=mock_driver)
    assert client.verify_connectivity() is True


def test_neo4j_client_execute_query_runs_in_session() -> None:
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    mock_record = MagicMock()
    mock_record.data.return_value = {"id": "CTR-001", "title": "Master Agreement"}
    mock_session.run.return_value = [mock_record]

    client = Neo4jClient(driver=mock_driver)
    results = client.execute_query("MATCH (c:Contract) RETURN c", {"limit": 1})

    assert len(results) == 1
    assert results[0]["id"] == "CTR-001"
    mock_session.run.assert_called_once_with("MATCH (c:Contract) RETURN c", {"limit": 1})


def test_neo4j_client_context_manager() -> None:
    mock_driver = MagicMock()
    with patch("app.graph.client.GraphDatabase.driver", return_value=mock_driver):
        with Neo4jClient() as client:
            assert client.driver == mock_driver
        mock_driver.close.assert_called_once()
