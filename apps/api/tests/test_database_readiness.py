from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app import main
from app.core import database
from app.modules.administration import service


@pytest.fixture(autouse=True)
def development_environment(monkeypatch):
    for key in ("APP_ENV", "VERCEL", "VERCEL_ENV"):
        monkeypatch.delenv(key, raising=False)


@pytest.mark.parametrize("environment", ({"APP_ENV": "production"}, {"VERCEL_ENV": "preview"}, {"VERCEL": "1"}))
def test_deployments_keep_postgresql_engine_when_connection_is_unavailable(monkeypatch, environment):
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(database.settings, "DATABASE_URL", "postgres://test@127.0.0.1:1/test")
    configured_engine = Mock()
    configured_engine.connect.side_effect = OperationalError("connect", {}, OSError())
    create_engine_mock = Mock(return_value=configured_engine)
    monkeypatch.setattr(database, "create_engine", create_engine_mock)

    assert database._create_database_engine() is configured_engine
    assert create_engine_mock.call_args.args[0].get_backend_name() == "postgresql"
    assert create_engine_mock.call_count == 1
    configured_engine.connect.assert_not_called()


def test_production_rejects_explicit_sqlite(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setattr(database.settings, "DATABASE_URL", "sqlite://")
    create_engine_mock = Mock()
    monkeypatch.setattr(database, "create_engine", create_engine_mock)

    assert database._create_database_engine() is None
    create_engine_mock.assert_not_called()


def test_development_still_uses_local_sqlite_when_postgres_fails(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("VERCEL_ENV", "development")
    monkeypatch.setattr(database.settings, "DATABASE_URL", "postgresql://test@127.0.0.1:1/test")
    postgres = Mock()
    postgres.connect.side_effect = OperationalError("connect", {}, OSError())
    sqlite = Mock()
    create_engine_mock = Mock(side_effect=[postgres, sqlite])
    monkeypatch.setattr(database, "create_engine", create_engine_mock)

    assert database._create_database_engine() is sqlite
    assert create_engine_mock.call_args.args[0].startswith("sqlite:///")
    postgres.dispose.assert_called_once()


def test_health_and_database_routes_return_503_when_postgresql_is_down(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    engine = create_engine("postgresql://test@127.0.0.1:1/test", connect_args={"connect_timeout": 1})
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", lambda: Session(engine))
    neo4j_health = AsyncMock()
    ollama_health = AsyncMock()
    monkeypatch.setattr(service, "check_neo4j_health", neo4j_health)
    monkeypatch.setattr(service.ollama_client, "check_health", ollama_health)

    try:
        with TestClient(main.app) as client:
            detail = client.get("/api/v1/admin/health")
            assert detail.status_code == 503
            assert detail.json()["database"] == {"status": "unhealthy", "backend": "postgresql"}
            assert detail.json()["status"] == "degraded"
            assert client.get("/health").status_code == 503
            assert client.get("/api/v1/universities").status_code == 503
            assert len(client.get("/data/school_details.json").json()) == 126
        neo4j_health.assert_not_awaited()
        ollama_health.assert_not_awaited()
    finally:
        engine.dispose()


def test_local_health_identifies_sqlite_and_keeps_optional_services_separate(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setattr(database, "SessionLocal", lambda: Session(engine))
    monkeypatch.setattr(service, "check_neo4j_health", AsyncMock(return_value={"status": "unhealthy"}))
    monkeypatch.setattr(service.ollama_client, "check_health", AsyncMock(return_value={"status": "offline"}))

    try:
        with TestClient(main.app) as client:
            detail = client.get("/api/v1/admin/health")
            assert detail.status_code == 200
            assert detail.json()["database"] == {"status": "healthy", "backend": "sqlite"}
            assert detail.json()["neo4j"]["status"] == "unhealthy"
            assert client.get("/health").status_code == 200
    finally:
        engine.dispose()
