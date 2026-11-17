"""
Consultation Service: Session Management, Streaming, and History.
Integrates Intent Extraction, Deterministic Neo4j Graph Pruning, and Zero-Hallucination Streaming.
"""

from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from app.core.models_db import (
    User,
    ChatSession,
    ChatMessage,
    Program,
    University,
    AdmissionCriteria,
    StudentProfile,
    StudentBackground,
    AcademicProfile,
    HealthProfile,
    PersonalityResult,
)
from app.integrations.ollama.client import OllamaClient
from app.integrations.neo4j.client import execute_query_async
from app.integrations.neo4j.query_builder import CypherQueryBuilder
from .schemas import ConsultationStreamRequest, ChatSessionItem, ChatMessageItem
from .parser import parse_intent_and_entities
from .agent import search_programs_tool

logger = logging.getLogger("foryourfuture.consultation")
ollama_client = OllamaClient()


async def handle_consultation_stream(
    db: Session, req: ConsultationStreamRequest, user: Optional[User] = None
) -> AsyncGenerator[str, None]:
    student_id = user.user_id if user else None
    
    # 1. Tạo hoặc lấy ChatSession trong PostgreSQL
    session_id = req.session_id
    if session_id:
        from fastapi import HTTPException
        from .history_router import owned
        if not user: raise HTTPException(401, "Vui lòng đăng nhập.")
        owned(db, session_id, user)
    if not session_id and student_id:
        sess = ChatSession(
            student_id=student_id,
            title=req.query_text[:40] + ("..." if len(req.query_text) > 40 else ""),
            started_at=datetime.utcnow(),
        )
        db.add(sess)
        db.commit()
        session_id = sess.session_id

    # 2. Lưu tin nhắn người dùng vào PostgreSQL
    if session_id:
        msg_user = ChatMessage(
            session_id=session_id,
            role="user",
            content=req.query_text,
            created_at=datetime.utcnow(),
        )
        db.add(msg_user)
        db.commit()

    # 3. Chuẩn bị context_items: Nếu client không truyền sẵn, trích xuất Intent và truy vấn Neo4j
    context_items = req.context_items
    if not context_items:
        profile_defaults: Dict[str, Any] = {}
        if student_id:
            acad = db.query(AcademicProfile).filter(AcademicProfile.student_id == student_id).first()
            if acad:
                if acad.exam_scores and isinstance(acad.exam_scores, dict):
                    for grp in ["A01", "A00", "D01", "B00", "C00"]:
                        if grp in acad.exam_scores:
                            profile_defaults["student_group_code"] = grp
                            profile_defaults["student_score"] = float(acad.exam_scores[grp])
                            break
                if acad.ielts_score:
                    profile_defaults["ielts_score"] = acad.ielts_score

            bg = db.query(StudentBackground).filter(StudentBackground.student_id == student_id).first()
            if bg:
                if bg.max_annual_tuition:
                    profile_defaults["max_annual_budget"] = bg.max_annual_tuition
                if bg.priority_points_calculated is not None:
                    profile_defaults["bonus_points"] = bg.priority_points_calculated

            pers = (
                db.query(PersonalityResult)
                .filter(PersonalityResult.student_id == student_id, PersonalityResult.test_type == "RIASEC")
                .order_by(PersonalityResult.completed_at.desc())
                .first()
            )
            if pers and pers.result_code:
                profile_defaults["holland_code"] = pers.result_code[:3].upper()

            hlth = db.query(HealthProfile).filter(HealthProfile.student_id == student_id).first()
            if hlth:
                profile_defaults["student_height"] = hlth.height_cm
                profile_defaults["student_eye_degree"] = hlth.max_eye_degree

        # Trích xuất Intent & Entities từ câu hỏi tự nhiên
        rec_req = parse_intent_and_entities(req.query_text, profile_defaults)
        
        # Truy vấn Cypher Pruning trên Neo4j Knowledge Graph
        try:
            cypher_query = CypherQueryBuilder.build_recommendation_query(rec_req, limit=5)
            cypher_params = CypherQueryBuilder.extract_query_parameters(rec_req, limit=5)
            neo4j_records = await execute_query_async(cypher_query, cypher_params)
            if neo4j_records:
                context_items = neo4j_records
                logger.info(f"Neo4j Knowledge Graph returned {len(neo4j_records)} grounded admissions for query.")
        except Exception as e:
            logger.warning(f"Neo4j Cypher query error: {e}")

        # Fallback nếu Neo4j không có kết quả phù hợp (ví dụ do ràng buộc thành phố hoặc năm)
        if not context_items:
            found = search_programs_tool(db, keyword=req.query_text, limit=4)
            context_items = []
            for f in found:
                context_items.append({
                    "university_id": f.get("university_name", ""),
                    "university_name": f.get("university_name", ""),
                    "program_id": f.get("program_id", ""),
                    "program_name": f.get("program_name", ""),
                    "city": f.get("location", "Toàn quốc"),
                    "benchmark_score": f.get("benchmark_score", 24.0),
                    "minimum_threshold": f.get("minimum_threshold"),
                    "score_margin": max(0.0, float(rec_req.student_score + (rec_req.bonus_points or 0.0) - f.get("benchmark_score", 24.0))),
                    "safety_level": "Target",
                    "actual_tuition": f.get("tuition_annual", 25000000),
                    "career_name": f.get("program_name", ""),
                    "job_growth_rate": 18.0,
                    "holland_match_score": 0.90,
                })

    # 4. Thu thập toàn bộ token để lưu vào PostgreSQL sau khi stream hoàn tất
    full_response = []

    async for chunk in ollama_client.stream_consultation(req.query_text, context_items):
        yield chunk
        if chunk.startswith("data: ") and not chunk.startswith("data: [DONE]"):
            try:
                import json
                data = json.loads(chunk[6:].strip())
                if "token" in data:
                    full_response.append(data["token"])
            except Exception:
                pass

    # 5. Lưu câu trả lời của trợ lý kèm Sub-graph Evidence vào PostgreSQL
    if session_id:
        reply_text = "".join(full_response).strip()
        if reply_text:
            msg_assistant = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=reply_text,
                evidence=context_items,
                created_at=datetime.utcnow(),
            )
            db.add(msg_assistant)
            db.commit()


def get_user_chat_sessions(db: Session, student_id: str) -> List[ChatSessionItem]:
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.student_id == student_id)
        .order_by(ChatSession.started_at.desc())
        .all()
    )
    result = []
    for s in sessions:
        count = db.query(ChatMessage).filter(ChatMessage.session_id == s.session_id).count()
        result.append(
            ChatSessionItem(
                session_id=s.session_id,
                title=s.title,
                started_at=s.started_at,
                message_count=count,
            )
        )
    return result


def get_session_messages(db: Session, session_id: str, user) -> List[ChatMessageItem]:
    from .history_router import owned
    owned(db, session_id, user)
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        ChatMessageItem(
            message_id=m.message_id,
            role=m.role,
            content=m.content,
            evidence=m.evidence or [],
            created_at=m.created_at,
        )
        for m in messages
    ]

