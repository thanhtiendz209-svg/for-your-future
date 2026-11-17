"""
Consultation Schemas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ConsultationStreamRequest(BaseModel):
    query_text: str = Field(..., min_length=2, description="Câu hỏi hoặc tâm sự của thí sinh")
    context_items: Optional[List[Dict[str, Any]]] = Field(
        default=None, 
        description="Danh sách các ngành/trường đã được lọc tất định từ trang kết quả"
    )
    session_id: Optional[str] = None


class ChatMessageItem(BaseModel):
    message_id: str
    role: str
    content: str
    evidence: List[Dict[str, Any]] = []
    created_at: datetime


class ChatSessionItem(BaseModel):
    session_id: str
    title: str
    started_at: datetime
    message_count: int = 0

