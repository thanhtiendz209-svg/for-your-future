"""
GraphRAG Router: Natural Language Intent Parsing, Graph Knowledge Retrieval,
MCDM Portfolio Ranking, and Streaming Gemini Consultation via LangGraph Agent.
"""

import json
from contextlib import aclosing
import uuid
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models_db import (
    User,
    AcademicProfile,
    StudentBackground,
    PersonalityResult,
    HealthProfile,
    StudentProfile
)
from app.modules.auth.service import get_current_user
from .models import (
    ChatPromptRequest,
    PortfolioRecommendationResponse,
    RecommendationResultItem,
)
from app.agent import career_advisory_service

logger = logging.getLogger("foryourfuture.graphrag")

router = APIRouter(prefix="/chat", tags=["GraphRAG Chat & Recommendation Engine"])


def extract_user_profile_data(db: Session, user: Optional[User]) -> Optional[Dict[str, Any]]:
    """Trích xuất dữ liệu hồ sơ học sinh từ PostgreSQL nếu user đã đăng nhập"""
    if not user:
        return None

    student_id = user.user_id
    profile_data: Dict[str, Any] = {"student_id": student_id}

    # 1. Profile cơ bản
    p = db.query(StudentProfile).filter(StudentProfile.student_id == student_id).first()
    if p:
        profile_data["first_name"] = p.first_name
        profile_data["last_name"] = p.last_name
        profile_data["grade_level"] = p.grade_level
        profile_data["target_year"] = p.target_year

    # 2. Học bạ / Điểm thi
    acad = db.query(AcademicProfile).filter(AcademicProfile.student_id == student_id).first()
    if acad:
        exam_scores = acad.exam_scores if isinstance(acad.exam_scores, dict) else {}
        profile_data["academic"] = {
            "exam_scores": exam_scores,
            "ielts_score": acad.ielts_score,
            "gpa_overall": acad.gpa_overall
        }

    # 3. Hoàn cảnh / Quê quán / Học phí
    bg = db.query(StudentBackground).filter(StudentBackground.student_id == student_id).first()
    if bg:
        profile_data["background"] = {
            "hometown_province": bg.hometown_province,
            "max_annual_tuition": bg.max_annual_tuition,
            "priority_points_calculated": bg.priority_points_calculated
        }

    # 4. Kết quả RIASEC mới nhất
    pers = db.query(PersonalityResult).filter(
        PersonalityResult.student_id == student_id,
        PersonalityResult.test_type == "RIASEC"
    ).order_by(PersonalityResult.completed_at.desc()).first()
    if pers:
        profile_data["personality"] = {"holland_code": pers.result_code}

    # 5. Thể lực
    hlth = db.query(HealthProfile).filter(HealthProfile.student_id == student_id).first()
    if hlth:
        profile_data["health"] = {
            "height_cm": hlth.height_cm,
            "max_eye_degree": hlth.max_eye_degree
        }

    return profile_data


@router.post(
    "/recommend",
    summary="Tách prompt -> Truy vấn Graph -> Ranking đa tiêu chí (JSON)",
    description="Nhận câu hỏi tự do, bóc tách thông tin qua LangGraph StateGraph, truy vấn Neo4j và xếp hạng danh mục Reach - Target - Safe."
)
async def chat_recommend(
    request: ChatPromptRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pipeline trọn vẹn từ prompt tự do đến danh mục khuyến nghị xếp hạng (hỗ trợ gọi API JSON)"""
    try:
        prompt_text = getattr(request, "prompt", None) or (request.get_prompt_text() if hasattr(request, "get_prompt_text") else str(request))
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        profile_data = extract_user_profile_data(db, user)

        res = await career_advisory_service.get_advisory_recommendation(
            prompt=prompt_text,
            session_id=session_id,
            history=request.conversation if hasattr(request, "conversation") else None,
            profile_data=profile_data
        )
        return res

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat_recommend pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi quy trình GraphRAG: {str(e)}"
        )


@router.post(
    "/recommend/stream",
    summary="Tách prompt -> Truy vấn Graph -> Ranking đa tiêu chí -> AI Stream (SSE)",
    description="Nhận prompt tự nhiên, tự động bóc tách qua LangGraph, xếp hạng danh mục nguyện vọng và sinh lời tư vấn AI trực tiếp qua Server-Sent Events (SSE)."
)
async def chat_recommend_stream(
    request: ChatPromptRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pipeline trọn vẹn trả về Server-Sent Events kèm intent, portfolio cards, clarification và lời tư vấn gõ chữ"""
    try:
        prompt_text = getattr(request, "prompt", None) or (request.get_prompt_text() if hasattr(request, "get_prompt_text") else str(request))
        session_id = f"stream_{uuid.uuid4().hex[:8]}"
        profile_data = extract_user_profile_data(db, user)

        async def event_generator():
            yield ": ready\n\n"
            flow = career_advisory_service.run_advisory_flow(
                prompt=prompt_text,
                session_id=session_id,
                history=request.conversation if hasattr(request, "conversation") else None,
                profile_data=profile_data,
            )
            try:
                async with aclosing(flow):
                    async for item in flow:
                        kind = item.get("type")
                        if kind == "done":
                            yield "data: [DONE]\n\n"
                            return
                        if kind in ("intent", "portfolio", "clarification", "token", "interrupted"):
                            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                        if kind == "interrupted":
                            return
            except Exception:
                logger.exception("Error streaming advisory recommendation")
            yield 'data: {"type":"interrupted","reason":"connection"}\n\n'

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Content-Type": "text/event-stream; charset=utf-8"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat_recommend_stream: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khởi tạo luồng tư vấn GraphRAG: {str(e)}"
        )
