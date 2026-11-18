"""Manage database engines, request sessions, and database readiness."""

import logging
import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import ArgumentError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .config import settings
from .models_db import Base

logger = logging.getLogger("foryourfuture.database")


def _requires_postgresql() -> bool:
    vercel_env = os.getenv("VERCEL_ENV")
    return (
        os.getenv("APP_ENV", "").strip().lower() in {"production", "preview"}
        or vercel_env in {"production", "preview"}
        or (not vercel_env and os.getenv("VERCEL") == "1")
    )


def _create_database_engine() -> Engine | None:
    requires_postgresql = _requires_postgresql()
    try:
        configured_url = settings.DATABASE_URL
        if configured_url.startswith("postgres://"):
            configured_url = configured_url.replace("postgres://", "postgresql://", 1)
        url = make_url(configured_url)
        backend = url.get_backend_name()
        if backend == "postgresql" and url.password != "your_aiven_password_here":
            configured_engine = create_engine(
                url,
                pool_size=10,
                max_overflow=20,
                pool_recycle=1800,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 5},
            )
            if requires_postgresql:
                # A disconnected production engine can retry on subsequent requests.
                return configured_engine

            try:
                with configured_engine.connect():
                    pass
            except SQLAlchemyError:
                configured_engine.dispose()
                raise
            return configured_engine
        if backend == "sqlite" and not requires_postgresql:
            return create_engine(url, connect_args={"check_same_thread": False})
        raise ArgumentError("A PostgreSQL connection is required.")
    except (SQLAlchemyError, ImportError) as error:
        if requires_postgresql:
            logger.error("PostgreSQL configuration is unavailable (%s).", type(error).__name__)
            return None
        logger.warning("PostgreSQL unavailable. Using local SQLite (%s).", type(error).__name__)
        sqlite_path = Path(__file__).resolve().parents[2] / "foryourfuture.db"
        return create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})


engine = _create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def database_health(db: Session):
    backend = "postgresql" if _requires_postgresql() else "unconfigured"
    try:
        backend = db.get_bind().dialect.name
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return {"status": "unhealthy", "backend": backend}
    return {"status": "healthy", "backend": backend}


def init_db():
    """Create tables and load the admissions catalog when the database is available."""
    if engine is None:
        return
    try:
        Base.metadata.create_all(bind=engine)
        from app.modules.consultation.history_migration import ensure_chat_owner
        from .seed import seed_initial_data

        ensure_chat_owner(engine)
        with SessionLocal() as db:
            seed_initial_data(db)
        logger.info("Database initialized (%s).", engine.dialect.name)
    except SQLAlchemyError as error:
        logger.warning("Database initialization failed (%s).", type(error).__name__)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db
