"""
Administration Service.
"""

import asyncio

from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from app.core.database import database_health
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
    db_status = await run_in_threadpool(database_health, db)
    if db_status["status"] == "unhealthy":
        return SystemHealthResponse(
            status="degraded",
            database=db_status,
            neo4j={"status": "not_checked"},
            ollama={"status": "not_checked"},
        )

    neo4j_status, ollama_status = await asyncio.gather(
        check_neo4j_health(), ollama_client.check_health()
    )

    return SystemHealthResponse(
        status="healthy",
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

