"""
Career Advisory Service: Core GraphRAG Conversational Intelligence Service.
Tuân thủ nghiêm ngặt Unified Flow:
  1. LLM Trích xuất (NLU Slot & Intent Extraction via Google Gemini Flash Lite)
  2. LangGraph StateGraph (Routing + Neo4j Cypher Pruning + MCDM Multi-criteria 3-Tier Ranking)
  3. LLM Làm mịn (Context-grounded Streaming Consultation & Zero-hallucination Advice)

Module được thiết kế độc lập, chuẩn hóa dạng Service để bất kỳ backend, frontend,
endpoint HTTP, WebSocket, hoặc third-party service nào cũng có thể tái sử dụng dễ dàng.
"""

import logging
from contextlib import aclosing
from typing import Dict, Any, List, Optional, AsyncGenerator

try:
    from .graph import career_agent_app
    from app.modules.graphrag.llm_service import GeminiStreamInterrupted, stream_gemini_messages, stream_portfolio_tokens
except ImportError:
    try:
        from .graph import career_agent_app
        from ..modules.graphrag.llm_service import GeminiStreamInterrupted, stream_gemini_messages, stream_portfolio_tokens
    except ImportError:
        from agent.graph import career_agent_app
        from llm_service import GeminiStreamInterrupted, stream_gemini_messages, stream_portfolio_tokens

logger = logging.getLogger("graphrag.career_service")


class CareerAdvisoryService:
    """Dịch vụ Cố vấn Tuyển sinh & Hướng nghiệp Đồ thị Tri thức (GraphRAG Agent Service)"""

    def __init__(self):
        self.app = career_agent_app

    async def run_advisory_flow(
        self,
        prompt: str,
        session_id: str = "default_session",
        history: Optional[List[Dict[str, str]]] = None,
        profile_data: Optional[Dict[str, Any]] = None,
        *,
        prefer_native: bool = False,
        complete_response: bool = False,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Forward text during graph execution and report incomplete generations."""
        graph_config = {"configurable": {"thread_id": session_id}}
        initial_input = {
            "session_id": session_id,
            "student_id": "caller",
            "latest_user_prompt": prompt,
            "messages": history or [],
            "profile_data": profile_data,
            "prefer_native": prefer_native,
            "complete_response": complete_response,
        }
        logger.info("[CareerAdvisoryService] Running flow for session_id=%s", session_id)
        parts = []
        final_state = {}
        results = self.app.astream(initial_input, config=graph_config, stream_mode=["custom", "values"])
        try:
            async with aclosing(results):
                async for mode, data in results:
                    if mode == "custom":
                        parts.append(data["token"])
                        yield data
                    else:
                        final_state = data

            intent = final_state.get("intent", "RECOMMEND")
            clarification = final_state.get("clarification_question")
            portfolio = final_state.get("portfolio")
            slots = final_state.get("slots") or {}
            has_portfolio = portfolio and any(portfolio.get(tier) for tier in ("reach", "target", "safe"))

            if intent == "RECOMMEND" and clarification and final_state.get("missing_slots"):
                yield {"type": "clarification", "question": clarification}

            if not parts and intent == "RECOMMEND" and has_portfolio:
                yield {"type": "intent", "data": {
                    "raw_query": prompt,
                    "student_score": slots.get("student_score"),
                    "subject_group": slots.get("student_group_code"),
                    "preferred_majors": slots.get("target_major_keywords", []),
                    "preferred_locations": [slots.get("preferred_city") or "Toàn quốc"],
                    "max_tuition_million_vnd": int(slots["max_annual_budget"] / 1_000_000) if slots.get("max_annual_budget") else None,
                    "personality_holland_code": slots.get("inferred_holland_code"),
                }}
                yield {"type": "portfolio", "data": portfolio}
                target_portfolio = final_state.get("portfolio_obj") or portfolio
                tokens = stream_portfolio_tokens(
                    target_portfolio, prompt, slots=slots, prefer_native=prefer_native, complete_response=complete_response,
                )
                async with aclosing(tokens):
                    async for token in tokens:
                        parts.append(token)
                        yield {"type": "token", "token": token}
            elif not parts:
                reply = final_state.get("final_text")
                if intent == "RECOMMEND" and reply == "READY_FOR_PORTFOLIO_STREAM":
                    score = slots.get("student_score")
                    group = slots.get("student_group_code")
                    city = slots.get("preferred_city")
                    filters = [
                        f"{score:g} điểm" if isinstance(score, (int, float)) else None,
                        f"tổ hợp {group}" if group else None,
                        city,
                    ]
                    criteria = ", ".join(value for value in filters if value)
                    reply = (
                        "Dữ liệu tuyển sinh hiện tại chưa xác nhận được trường và ngành phù hợp"
                        + (f" với {criteria}." if criteria else ".")
                        + "\n\nBạn có thể xem điểm chuẩn theo khu vực và phương thức trong "
                        "[Bộ lọc tuyển sinh](https://foryourfuture.vercel.app/#huong-nghiep), "
                        "rồi đối chiếu tổ hợp và điều kiện trong đề án của từng trường."
                    )
                if reply and reply != "READY_FOR_PORTFOLIO_STREAM":
                    parts.append(reply)
                    yield {"type": "token", "token": reply}
                else:
                    messages = [
                        {"role": "system", "content": (
                            "Bạn là chuyên gia hướng nghiệp. Hãy tư vấn bằng tiếng Việt, "
                            "trình bày rõ ràng và chỉ dùng số liệu tuyển sinh khi có căn cứ."
                        )},
                        {"role": "user", "content": f"Câu hỏi của học sinh: {prompt}"},
                    ]
                    tokens = stream_gemini_messages(
                        messages, temperature=0.35, max_tokens=1000,
                        prefer_native=prefer_native, complete_response=complete_response,
                    )
                    async with aclosing(tokens):
                        async for token in tokens:
                            parts.append(token)
                            yield {"type": "token", "token": token}
        except GeminiStreamInterrupted as error:
            yield {"type": "interrupted", "reason": error.reason}
            return

        yield {"type": "done", "full_reply": "".join(parts)}

    async def get_advisory_recommendation(
        self,
        prompt: str,
        session_id: str = "default_session",
        history: Optional[List[Dict[str, str]]] = None,
        profile_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Hàm tiện ích dành cho các endpoint REST không dùng stream SSE (trả về JSON trọn gói).
        """
        intent_data = None
        portfolio_data = None
        clarification_data = None
        collected_tokens = []
        interruption = None

        async for event in self.run_advisory_flow(prompt, session_id, history, profile_data):
            ev_type = event.get("type")
            if ev_type == "intent":
                intent_data = event.get("data")
            elif ev_type == "portfolio":
                portfolio_data = event.get("data")
            elif ev_type == "clarification":
                clarification_data = event.get("question")
            elif ev_type == "token":
                collected_tokens.append(event.get("token", ""))
            elif ev_type == "interrupted":
                interruption = event["reason"]

        result = {
            "intent": intent_data,
            "portfolio": portfolio_data,
            "clarification_question": clarification_data,
            "advice": "".join(collected_tokens),
            "full_reply": "".join(collected_tokens)
        }
        if interruption:
            result["interruption"] = interruption
        return result


# Singleton instance sẵn sàng dùng chung cho mọi module
career_advisory_service = CareerAdvisoryService()
