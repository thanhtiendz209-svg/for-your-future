"""
Database Connection and Session Management for PostgreSQL (Aiven Cloud via psycopg2 / asyncpg).
Provides session factory, engine creation, and FastAPI dependency get_db.
"""

import os
import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import settings
from .models_db import Base

logger = logging.getLogger("foryourfuture.database")

# Dual-mode engine: Try PostgreSQL (Aiven Cloud); Fallback to SQLite (local zero-setup)
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=False
    )
    with engine.connect() as conn:
        pass
    logger.info("Connected to PostgreSQL successfully.")
except Exception as e:
    sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "foryourfuture.db"))
    logger.warning(f"PostgreSQL unreachable ({e}). Falling back to local SQLite at {sqlite_path}.")
    engine = create_engine(
        f"sqlite:///{sqlite_path}",
        connect_args={"check_same_thread": False},
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Tạo toàn bộ bảng CSDL trên PostgreSQL nếu chưa tồn tại và kích hoạt seed ban đầu"""
    try:
        Base.metadata.create_all(bind=engine)
        from app.modules.consultation.history_migration import ensure_chat_owner
        ensure_chat_owner(engine)
        logger.info("PostgreSQL database tables verified and initialized successfully.")
        
        # Tự động seed dữ liệu mẫu xác thực nếu CSDL còn trống
        from .seed import seed_initial_data
        with SessionLocal() as db:
            seed_initial_data(db)
    except Exception as e:
        logger.warning(f"Error connecting to DB (offline/sandboxed mode): {e}")
        return


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency cung cấp database session độc lập cho mỗi request"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

