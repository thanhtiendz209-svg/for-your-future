from datetime import timedelta
from secrets import token_hex

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import get_db
from app.core.models_db import Base, User
from app.core.security import create_access_token
from app import main
from app.modules.consultation import router as consultation
from app.modules.graphrag import router as graphrag


AI_ROUTES = (
    ("/api/v1/chat/recommend", {"prompt": "Tư vấn ngành học"}),
    ("/api/v1/chat/recommend/stream", {"prompt": "Tư vấn ngành học"}),
    ("/api/v1/consult/stream", {"query_text": "Tư vấn ngành học"}),
)


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([
            User(user_id="active", email="active@example.test", password_hash="fixture"),
            User(user_id="disabled", email="disabled@example.test", password_hash="fixture", is_active=False),
        ])
        db.commit()

    def get_test_db():
        with Session(engine) as db:
            yield db

    monkeypatch.setattr(settings, "SECRET_KEY", token_hex(32))
    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setitem(main.app.dependency_overrides, get_db, get_test_db)
    try:
        with TestClient(main.app) as test_client:
            yield test_client
    finally:
        engine.dispose()


def test_ai_routes_reject_missing_invalid_expired_and_inactive_tokens(client, monkeypatch):
    def reject_generation(*args, **kwargs):
        pytest.fail("Unauthorized request reached the AI pipeline")

    monkeypatch.setattr(graphrag.career_advisory_service, "get_advisory_recommendation", reject_generation)
    monkeypatch.setattr(graphrag.career_advisory_service, "run_advisory_flow", reject_generation)
    monkeypatch.setattr(consultation, "handle_consultation_stream", reject_generation)

    rejected_headers = (
        {},
        {"Authorization": "Bearer invalid"},
        {"Authorization": f"Bearer {create_access_token('active', expires_delta=timedelta(seconds=-30))}"},
        {"Authorization": f"Bearer {create_access_token('disabled')}"},
    )
    for path, body in AI_ROUTES:
        for headers in rejected_headers:
            assert client.post(path, json=body, headers=headers).status_code == 401


def test_authenticated_user_can_call_all_ai_routes(client, monkeypatch):
    async def recommend(*, profile_data, **kwargs):
        return {"student_id": profile_data["student_id"]}

    async def stream(*, profile_data, **kwargs):
        yield {"type": "token", "token": profile_data["student_id"]}

    async def consult(db, req, user):
        yield f"data: {user.user_id}\n\n"

    monkeypatch.setattr(graphrag.career_advisory_service, "get_advisory_recommendation", recommend)
    monkeypatch.setattr(graphrag.career_advisory_service, "run_advisory_flow", stream)
    monkeypatch.setattr(consultation, "handle_consultation_stream", consult)

    headers = {"Authorization": f"Bearer {create_access_token('active')}"}
    for path, body in AI_ROUTES:
        response = client.post(path, json=body, headers=headers)
        assert response.status_code == 200
        assert "active" in response.text

    assert client.get("/api/v1/universities").status_code == 200
