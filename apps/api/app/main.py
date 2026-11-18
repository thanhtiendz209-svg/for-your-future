"""
For Your Future - Main FastAPI Application.
Production-ready Modular Monolith with OpenAPI Contracts, CORS, and Lifespan Management.
"""

import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db
from app.integrations.neo4j.client import close_driver
from app.modules.auth.router import router as auth_router
from app.modules.consultation.history_router import router as chat_history_router
from app.modules.students.router import router as students_router
from app.modules.assessments.router import router as assessments_router
from app.modules.careers.router import router as careers_router
from app.modules.universities.router import router as universities_router
from app.modules.recommendations.router import router as recommendations_router
from app.modules.consultation.router import router as consultation_router
from app.modules.administration.router import router as administration_router
from app.modules.graphrag.router import router as graphrag_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("foryourfuture")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời khởi động và kết thúc của ứng dụng"""
    logger.info("Starting For Your Future API...")
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Database init notice: {e}")

    yield

    logger.info("Shutting down For Your Future API...")
    await close_driver()


app = FastAPI(
    title=settings.APP_NAME,
    description="Nền tảng trắc nghiệm, hướng nghiệp và tư vấn tuyển sinh đại học cho học sinh, sinh viên Việt Nam.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware gắn Request Timing và Request ID"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# Register Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(chat_history_router, prefix=settings.API_V1_STR)
app.include_router(students_router, prefix=settings.API_V1_STR)
app.include_router(assessments_router, prefix=settings.API_V1_STR)
app.include_router(careers_router, prefix=settings.API_V1_STR)
app.include_router(universities_router, prefix=settings.API_V1_STR)
app.include_router(recommendations_router, prefix=settings.API_V1_STR)
app.include_router(consultation_router, prefix=settings.API_V1_STR)
app.include_router(administration_router, prefix=settings.API_V1_STR)
app.include_router(graphrag_router, prefix=settings.API_V1_STR)


from pathlib import Path
from fastapi.staticfiles import StaticFiles

@app.get("/health", tags=["Root"])
def health_simple():
    return {"status": "ok", "timestamp": time.time()}


@app.get("/api", tags=["Root"])
def api_info():
    return {
        "app": settings.APP_NAME,
        "version": "2.0.0",
        "status": "online",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }


# Mount Web Public directory for full SPA frontend hosting
web_public_dir = Path(__file__).resolve().parent.parent.parent / "web" / "public"
if web_public_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_public_dir), html=True), name="static")


