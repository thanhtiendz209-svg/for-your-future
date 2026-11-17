"""
Administration Schemas.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class SystemHealthResponse(BaseModel):
    status: str
    database: Dict[str, Any]
    neo4j: Dict[str, Any]
    ollama: Dict[str, Any]


class SystemStatsResponse(BaseModel):
    universities_count: int
    programs_count: int
    careers_count: int
    users_count: int
    recommendation_runs_count: int
    chat_sessions_count: int

