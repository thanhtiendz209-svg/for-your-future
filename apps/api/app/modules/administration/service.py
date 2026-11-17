"""
Administration Service.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.core.models_db import (
    University,
    Program,
    Career,
    User,
    RecommendationRun,
    ChatSession,
)
from app.integrations.neo4j.client import check_health as check_neo4j_health
from app.integrations.ollama.client import OllamaClient
from .schemas import SystemHealthResponse, SystemStatsResponse

ollama_client = OllamaClient()


async def get_system_health(db: Session) -> SystemHealthResponse:
    # 1. Kiểm tra Relational Database
    db_status = {"status": "unhealthy"}
    try:
        db.execute(text("SELECT 1"))
        db_status = {
            "status": "healthy",
            "url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL,
        }
    except Exception as e:
        db_status = {"status": "unhealthy", "error": str(e)}

    # 2. Kiểm tra Neo4j
    neo4j_status = await check_neo4j_health()

    # 3. Kiểm tra Ollama
    ollama_status = await ollama_client.check_health()

    overall = "healthy"
    if db_status.get("status") != "healthy":
        overall = "degraded"

    return SystemHealthResponse(
        status=overall,
        database=db_status,
        neo4j=neo4j_status,
        ollama=ollama_status,
    )


def get_system_stats(db: Session) -> SystemStatsResponse:
    unis = db.query(University).count()
    progs = db.query(Program).count()
    careers = db.query(Career).count()
    users = db.query(User).count()
    runs = db.query(RecommendationRun).count()
    chats = db.query(ChatSession).count()

    return SystemStatsResponse(
        universities_count=unis,
        programs_count=progs,
        careers_count=careers,
        users_count=users,
        recommendation_runs_count=runs,
        chat_sessions_count=chats,
    )

