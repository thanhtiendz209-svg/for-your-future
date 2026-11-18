"""
Administration Router.
"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from .schemas import SystemHealthResponse, SystemStatsResponse
from .service import get_system_health, get_system_stats

router = APIRouter(prefix="/admin", tags=["Administration & Health"])


@router.get(
    "/health",
    response_model=SystemHealthResponse,
    responses={503: {"model": SystemHealthResponse}},
)
async def check_health_endpoint(response: Response, db: Session = Depends(get_db)):
    """Kiểm tra chi tiết trạng thái sức khỏe của PostgreSQL/SQLite, Neo4j, và Ollama"""
    result = await get_system_health(db)
    if result.database["status"] == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result


@router.get("/stats", response_model=SystemStatsResponse)
def get_stats_endpoint(db: Session = Depends(get_db)):
    """Thống kê tổng lượng dữ liệu trường học, chương trình, người dùng, và truy vấn"""
    return get_system_stats(db)

