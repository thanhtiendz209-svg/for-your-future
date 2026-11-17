"""
Consultation Router.
"""

from typing import List
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models_db import User
from app.modules.auth.service import get_current_user_optional, get_current_user
from .schemas import ConsultationStreamRequest, ChatSessionItem, ChatMessageItem
from .service import handle_consultation_stream, get_user_chat_sessions, get_session_messages

router = APIRouter(prefix="/consult", tags=["AI Consultation"])


@router.post("/stream")
async def stream_consultation_endpoint(
    req: ConsultationStreamRequest,
    user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Streaming câu trả lời tư vấn AI qua Server-Sent Events (SSE).
    Tự động áp dụng System Prompt chống ảo giác (Zero-Hallucination) và đối chiếu với dữ liệu Sub-graph.
    """
    generator = handle_consultation_stream(db, req, user)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/sessions", response_model=List[ChatSessionItem])
def list_sessions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy danh sách các phiên trò chuyện tư vấn của học sinh"""
    return get_user_chat_sessions(db, user.user_id)


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageItem])
def list_messages(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lấy toàn bộ lịch sử tin nhắn trong một phiên trò chuyện"""
    return get_session_messages(db, session_id, user)

