"""
Recommendation Router.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models_db import User
from app.modules.auth.service import get_current_user_optional, get_current_user
from .schemas import RecommendationRequest, RecommendationResponse
from .service import execute_recommendation, get_user_recommendation_history

router = APIRouter(prefix="/recommend", tags=["Recommendation Engine"])


@router.post("", response_model=RecommendationResponse)
def recommend(
    req: RecommendationRequest,
    limit: int = Query(15, ge=1, le=50),
    user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Thực hiện lọc tất định (Deterministic Pruning):
    Điểm chuẩn, Điểm sàn, Học phí thực tế, Chiều cao, Độ cận thị, Giới tính và Độ khớp Holland RIASEC.
    """
    return execute_recommendation(db, req, user=user, limit=limit)


@router.get("/history", response_model=List[Dict[str, Any]])
def get_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy lịch sử các lần chạy gợi ý nguyện vọng của học sinh"""
    return get_user_recommendation_history(db, user.user_id)

