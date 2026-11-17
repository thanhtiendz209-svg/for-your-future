"""
Assessments Router.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models_db import User
from app.modules.auth.service import get_current_user
from .schemas import (
    SavePersonalityRequest,
    PersonalityItemResponse,
    SaveCompetencyRequest,
    CompetencyResponse,
)
from .service import (
    save_personality_result,
    get_latest_personality,
    get_personality_history,
    save_competency_assessment,
)

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.post("/personality", response_model=PersonalityItemResponse, status_code=status.HTTP_201_CREATED)
def post_personality(
    req: SavePersonalityRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lưu kết quả bài trắc nghiệm tính cách (RIASEC, MBTI, Big Five)"""
    return save_personality_result(db, user.user_id, req)


@router.get("/personality/latest", response_model=Dict[str, Any])
def get_latest(
    test_type: Optional[str] = Query(None, description="Lọc theo loại: RIASEC, MBTI, BIGFIVE"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy kết quả trắc nghiệm mới nhất cho từng loại độc lập"""
    return get_latest_personality(db, user.user_id, test_type)


@router.get("/personality/history", response_model=List[PersonalityItemResponse])
def get_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách toàn bộ lịch sử các lần làm bài trắc nghiệm của học sinh"""
    return get_personality_history(db, user.user_id)


@router.post("/competency", response_model=CompetencyResponse, status_code=status.HTTP_201_CREATED)
def post_competency(
    req: SaveCompetencyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lưu kết quả bài thi Đánh giá năng lực / Đánh giá tư duy (V-ACT, HSA, TSA)"""
    return save_competency_assessment(db, user.user_id, req)

