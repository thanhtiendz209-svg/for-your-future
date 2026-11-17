"""
Recommendation Service.
"""

import time
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.core.models_db import (
    User,
    StudentProfile,
    StudentBackground,
    AcademicProfile,
    HealthProfile,
    PersonalityResult,
    RecommendationRun,
    QueryLog,
)
from .schemas import RecommendationRequest, RecommendationResponse
from .engine import run_deterministic_pruning


def execute_recommendation(
    db: Session, req: RecommendationRequest, user: Optional[User] = None, limit: int = 15
) -> RecommendationResponse:
    start_time = time.time()
    student_id = user.user_id if user else None

    # Tự động điền các trường còn thiếu từ hồ sơ người dùng nếu đã đăng nhập
    if user:
        profile = db.query(StudentProfile).filter(StudentProfile.student_id == user.user_id).first()
        bg = db.query(StudentBackground).filter(StudentBackground.student_id == user.user_id).first()
        hlth = db.query(HealthProfile).filter(HealthProfile.student_id == user.user_id).first()
        latest_riasec = (
            db.query(PersonalityResult)
            .filter(PersonalityResult.student_id == user.user_id, PersonalityResult.test_type == "RIASEC")
            .order_by(PersonalityResult.completed_at.desc())
            .first()
        )

        if profile and profile.gender and req.student_gender == "Male":
            req.student_gender = profile.gender
        if hlth and hlth.height_cm and req.student_height is None:
            req.student_height = hlth.height_cm
        if hlth and hlth.max_eye_degree and req.student_eye_degree is None:
            req.student_eye_degree = hlth.max_eye_degree
        if bg and bg.priority_points_calculated and (req.bonus_points == 0.0 or req.bonus_points is None):
            req.bonus_points = bg.priority_points_calculated
        if bg and bg.max_annual_tuition and req.max_annual_budget == 0:
            req.max_annual_budget = bg.max_annual_tuition
        if latest_riasec and not req.holland_code:
            req.holland_code = latest_riasec.result_code

    response = run_deterministic_pruning(db, req, limit=limit)
    latency_ms = round((time.time() - start_time) * 1000, 2)

    # Ghi nhận kết quả vào RecommendationRun và QueryLog
    try:
        run_record = RecommendationRun(
            student_id=student_id,
            profile_version=1,
            rule_version="deterministic_v2",
            input_params=req.dict(),
            results=[r.dict() for r in response.results],
        )
        db.add(run_record)

        log_record = QueryLog(
            student_id=student_id,
            query_text=f"Rec: Holland={req.holland_code}, Group={req.student_group_code}, Score={req.student_score}, Budget={req.max_annual_budget}",
            result_count=response.total_found,
            latency_ms=latency_ms,
        )
        db.add(log_record)
        db.commit()
    except Exception as e:
        db.rollback()

    return response


def get_user_recommendation_history(db: Session, student_id: str) -> List[Dict[str, Any]]:
    runs = (
        db.query(RecommendationRun)
        .filter(RecommendationRun.student_id == student_id)
        .order_by(RecommendationRun.created_at.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "run_id": r.run_id,
            "created_at": r.created_at.isoformat(),
            "input_params": r.input_params,
            "results_count": len(r.results) if isinstance(r.results, list) else 0,
            "results": r.results,
        }
        for r in runs
    ]
