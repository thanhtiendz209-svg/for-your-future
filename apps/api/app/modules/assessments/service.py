"""
Assessments Service.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.models_db import PersonalityResult, CompetencyAssessment
from .schemas import (
    SavePersonalityRequest,
    PersonalityItemResponse,
    SaveCompetencyRequest,
    CompetencyResponse,
)


def save_personality_result(
    db: Session, student_id: str, req: SavePersonalityRequest
) -> PersonalityItemResponse:
    """
    Lưu kết quả trắc nghiệm tính cách.
    Bảo toàn quy tắc Stage 1: MBTI và RIASEC lưu độc lập theo timestamp hoàn thành;
    Big Five không bao giờ ghi đè RIASEC/MBTI.
    """
    item = PersonalityResult(
        student_id=student_id,
        test_type=req.test_type.upper(),
        result_code=req.result_code.strip().upper(),
        scores_detail=req.scores_detail,
        top_traits=req.top_traits,
        title=req.title,
        summary=req.summary,
        completed_at=datetime.utcnow(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return PersonalityItemResponse(
        result_id=item.result_id,
        test_type=item.test_type,
        result_code=item.result_code,
        scores_detail=item.scores_detail,
        top_traits=item.top_traits or [],
        title=item.title,
        summary=item.summary,
        completed_at=item.completed_at,
    )


def get_latest_personality(
    db: Session, student_id: str, test_type: Optional[str] = None
) -> Dict[str, Any]:
    """Lấy kết quả trắc nghiệm mới nhất cho từng bài độc lập (RIASEC / MBTI / Big Five)."""
    query = db.query(PersonalityResult).filter(PersonalityResult.student_id == student_id)
    if test_type:
        query = query.filter(PersonalityResult.test_type == test_type.upper())
    
    results = query.order_by(PersonalityResult.completed_at.desc()).all()
    
    latest_by_type: Dict[str, Any] = {}
    for r in results:
        t = r.test_type
        if t not in latest_by_type:
            latest_by_type[t] = {
                "result_id": r.result_id,
                "test_type": r.test_type,
                "result_code": r.result_code,
                "scores_detail": r.scores_detail,
                "top_traits": r.top_traits or [],
                "title": r.title,
                "summary": r.summary,
                "completed_at": r.completed_at.isoformat(),
            }
    return latest_by_type


def get_personality_history(
    db: Session, student_id: str
) -> List[PersonalityItemResponse]:
    """Xem lịch sử tất cả các lần làm bài."""
    items = (
        db.query(PersonalityResult)
        .filter(PersonalityResult.student_id == student_id)
        .order_by(PersonalityResult.completed_at.desc())
        .all()
    )
    return [
        PersonalityItemResponse(
            result_id=i.result_id,
            test_type=i.test_type,
            result_code=i.result_code,
            scores_detail=i.scores_detail,
            top_traits=i.top_traits or [],
            title=i.title,
            summary=i.summary,
            completed_at=i.completed_at,
        )
        for i in items
    ]


def save_competency_assessment(
    db: Session, student_id: str, req: SaveCompetencyRequest
) -> CompetencyResponse:
    """Lưu kết quả Đánh giá năng lực (V-ACT / HSA / TSA)."""
    percentile = None
    if req.max_scale > 0:
        percentile = round((req.total_score / req.max_scale) * 100, 1)

    item = CompetencyAssessment(
        student_id=student_id,
        test_type=req.test_type.upper(),
        quant_score=req.quant_score,
        verbal_score=req.verbal_score,
        logic_score=req.logic_score,
        data_analysis_score=req.data_analysis_score,
        total_score=req.total_score,
        max_scale=req.max_scale,
        percentile=percentile,
        completed_at=datetime.utcnow(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return CompetencyResponse(
        assessment_id=item.assessment_id,
        test_type=item.test_type,
        quant_score=item.quant_score,
        verbal_score=item.verbal_score,
        logic_score=item.logic_score,
        data_analysis_score=item.data_analysis_score,
        total_score=item.total_score,
        max_scale=item.max_scale,
        percentile=item.percentile,
        completed_at=item.completed_at,
    )

