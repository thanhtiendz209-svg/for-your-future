"""
Application Configuration for For Your Future API.
Supports environment variables with production-ready defaults and local fallbacks.
"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "For Your Future"
    PROJECT_NAME: str = "for-your-future"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "for_your_future_secure_jwt_secret_key_minimum_32_bytes_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Databases - PostgreSQL (Aiven Cloud via psycopg2 / asyncpg with SSL require)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://avnadmin:your_aiven_password_here@pg-1a5f2827-thanhtiendz209-1f86.b.aivencloud.com:26350/defaultdb?sslmode=require"
    )
    ASYNC_DATABASE_URL: str = os.getenv(
        "ASYNC_DATABASE_URL",
        "postgresql+asyncpg://avnadmin:your_aiven_password_here@pg-1a5f2827-thanhtiendz209-1f86.b.aivencloud.com:26350/defaultdb"
    )
    
    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "sitk2023")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")
    
    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    OLLAMA_TIMEOUT_SECONDS: int = 45

    # Google Gemini AI (Primary Conversational Agent Provider)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    GEMINI_OPENAI_BASE_URL: str = os.getenv(
        "GEMINI_OPENAI_BASE_URL", 
        "https://generativelanguage.googleapis.com/v1beta/openai"
    )
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ]

    class Config:
        env_file = str(Path(__file__).resolve().parents[2] / ".env")
        case_sensitive = True


settings = Settings()

