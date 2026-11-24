"""
State definition for LangGraph Conversational Career Guidance Agent.
"""

from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict, total=False):
    session_id: str
    student_id: str
    messages: List[Dict[str, str]]
    latest_user_prompt: str
    intent: str  # RECOMMEND, COMPARE, LOOKUP, CHITCHAT, OUT_OF_SCOPE
    profile_data: Optional[Dict[str, Any]]  # Full profile from PostgreSQL
    prefer_native: bool
    complete_response: bool
    slots: Dict[str, Any]  # Persistent slot dictionary
    missing_slots: List[str]  # Missing required slots
    clarification_question: Optional[str]
    raw_candidates: List[Any]
    portfolio: Optional[Dict[str, Any]]
    portfolio_obj: Optional[Any]
    intent_obj: Optional[Any]
    final_response_tokens: List[str]
    final_text: str
