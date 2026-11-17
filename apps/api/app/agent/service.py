"""
Career Advisory Service: Core GraphRAG Conversational Intelligence Service.
Tuân thủ nghiêm ngặt Unified Flow:
  1. LLM Trích xuất (NLU Slot & Intent Extraction via Google Gemini Flash Lite)
  2. LangGraph StateGraph (Routing + Neo4j Cypher Pruning + MCDM Multi-criteria 3-Tier Ranking)
  3. LLM Làm mịn (Context-grounded Streaming Consultation & Zero-hallucination Advice)

Module được thiết kế độc lập, chuẩn hóa dạng Service để bất kỳ backend, frontend,
endpoint HTTP, WebSocket, hoặc third-party service nào cũng có thể tái sử dụng dễ dàng.
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator

try:
    from .graph import career_agent_app
    from app.modules.graphrag.llm_service import stream_portfolio_ai_consultation, call_gemini_chat
except ImportError:
    try:
        from .graph import career_agent_app
        from ..modules.graphrag.llm_service import stream_portfolio_ai_consultation, call_gemini_chat
    except ImportError:
        from agent.graph import career_agent_app
        from llm_service import stream_portfolio_ai_consultation, call_gemini_chat

logger = logging.getLogger("graphrag.career_service")


class CareerAdvisoryService:
    """Dịch vụ Cố vấn Tuyển sinh & Hướng nghiệp Đồ thị Tri thức (GraphRAG Agent Service)"""

    def __init__(self):
        self.app = career_agent_app

    async def _generate_fallback_consultation(self, prompt: str, slots: Dict[str, Any]) -> str:
        """Sinh lời tư vấn dự phòng trực tiếp qua Gemini khi đồ thị không khớp dữ liệu cứng."""
        try:
            sys_msg = (
                "Bạn là Chuyên gia Cố vấn Tuyển sinh Đại học & Định hướng Nghề nghiệp AI của hệ thống GraphRAG. "
                "Hãy giải đáp chi tiết, thấu hiểu, mang tính định hướng cao và truyền cảm hứng cho học sinh về câu hỏi sau. "
                "Trình bày chuyên nghiệp bằng định dạng Markdown với các gạch đầu dòng rõ ràng."
            )
            resp = await call_gemini_chat([
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": f"Câu hỏi của học sinh: {prompt}"}
            ], temperature=0.35, max_tokens=1000)
            if resp:
                return resp
        except Exception as e:
            logger.warning(f"Fallback generation error: {e}")
        return "Chào bạn! Mình đã tiếp nhận câu hỏi của bạn. Bạn hãy chia sẻ thêm về điểm thi dự kiến, khối thi hoặc ngành nghề mong muốn để mình tư vấn chi tiết nhất nhé!"

    async def run_advisory_flow(
        self,
        prompt: str,
        session_id: str = "default_session",
        history: Optional[List[Dict[str, str]]] = None,
        profile_data: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Thực thi trọn vẹn quy trình 3 bước chuẩn hóa:
        1. LLM Trích xuất (Entity, Slots, Intent)
        2. LangGraph StateGraph + Neo4j Graph Query + MCDM Ranking
        3. LLM Làm mịn (Streaming token tư vấn)
        
        Trả về AsyncGenerator các sự kiện dạng dictionary:
          - {"type": "intent", "data": {...}}
          - {"type": "portfolio", "data": {...}}
          - {"type": "clarification", "question": "..."}
          - {"type": "token", "token": "..."}
          - {"type": "done", "full_reply": "..."}
        """
        graph_config = {"configurable": {"thread_id": session_id}}

        initial_input = {
            "session_id": session_id,
            "student_id": "caller",
            "latest_user_prompt": prompt,
            "messages": history or [],
            "profile_data": profile_data
        }

        logger.info(f"[CareerAdvisoryService] Running flow for session_id={session_id}")
        final_state = await self.app.ainvoke(initial_input, config=graph_config)

        intent = final_state.get("intent", "RECOMMEND")
        clarification_q = final_state.get("clarification_question")
        portfolio_dict = final_state.get("portfolio")
        portfolio_obj = final_state.get("portfolio_obj")
        slots = final_state.get("slots", {})

        full_reply = ""

        # TRƯỜNG HỢP 1: Cần hỏi lại (Thiếu điểm / khối khi muốn tư vấn đề xuất nguyện vọng)
        if intent not in ("LOOKUP", "CHITCHAT", "OUT_OF_SCOPE") and (final_state.get("missing_slots") or not portfolio_dict) and clarification_q:
            logger.info(f"[CareerAdvisoryService] Clarification required: {clarification_q}")
            yield {"type": "clarification", "question": clarification_q}

            words = clarification_q.split(" ")
            for i, w in enumerate(words):
                token = w if i == len(words) - 1 else w + " "
                full_reply += token
                yield {"type": "token", "token": token}
                await asyncio.sleep(0.01)

            yield {"type": "done", "full_reply": full_reply}
            return

        # TRƯỜNG HỢP 2: Tra cứu trực tiếp (LOOKUP), So sánh (COMPARE), Chào hỏi hoặc Ngoài phạm vi
        has_valid_portfolio = bool(portfolio_dict and (portfolio_dict.get("reach") or portfolio_dict.get("target") or portfolio_dict.get("safe")))

        if intent in ("CHITCHAT", "OUT_OF_SCOPE", "LOOKUP", "COMPARE") or not has_valid_portfolio:
            text_reply = final_state.get("final_text")

            # Tuyệt đối không bao giờ stream chuỗi token kỹ thuật nội bộ
            if not text_reply or text_reply == "READY_FOR_PORTFOLIO_STREAM":
                if has_valid_portfolio and intent == "RECOMMEND":
                    # Trường hợp đề xuất hợp lệ có danh mục -> chuyển sang Case 3
                    pass
                else:
                    text_reply = await self._generate_fallback_consultation(prompt, slots)

            if text_reply and text_reply != "READY_FOR_PORTFOLIO_STREAM":
                words = text_reply.split(" ")
                for i, w in enumerate(words):
                    token = w if i == len(words) - 1 else w + " "
                    full_reply += token
                    yield {"type": "token", "token": token}
                    await asyncio.sleep(0.01)

                yield {"type": "done", "full_reply": full_reply}
                return

        # TRƯỜNG HỢP 3: Đủ thông tin -> Bắn Intent, Thẻ Nguyện Vọng 3 Tầng & Stream LLM Làm mịn
        intent_data = {
            "raw_query": prompt,
            "student_score": slots.get("student_score"),
            "subject_group": slots.get("student_group_code"),
            "preferred_majors": slots.get("target_major_keywords", []),
            "preferred_locations": [slots.get("preferred_city")] if slots.get("preferred_city") else ["Toàn quốc"],
            "max_tuition_million_vnd": int(slots.get("max_annual_budget", 0) / 1_000_000) if slots.get("max_annual_budget") else None,
            "personality_holland_code": slots.get("inferred_holland_code")
        }
        yield {"type": "intent", "data": intent_data}
        yield {"type": "portfolio", "data": portfolio_dict}

        # 3. LLM Làm mịn: Sinh lời tư vấn trực tiếp qua Gemini
        target_portfolio = portfolio_obj if portfolio_obj is not None else portfolio_dict
        async for chunk in stream_portfolio_ai_consultation(target_portfolio, prompt, slots=slots):
            if chunk.startswith("data: ") and not chunk.startswith("data: [DONE]"):
                try:
                    inner = json.loads(chunk[6:].strip())
                    token = inner.get("token", "")
                    if token:
                        full_reply += token
                        yield {"type": "token", "token": token}
                except Exception:
                    pass
            elif not chunk.startswith("data:"):
                full_reply += chunk
                yield {"type": "token", "token": chunk}

        yield {"type": "done", "full_reply": full_reply}

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

        return {
            "intent": intent_data,
            "portfolio": portfolio_data,
            "clarification_question": clarification_data,
            "advice": "".join(collected_tokens),
            "full_reply": "".join(collected_tokens)
        }


# Singleton instance sẵn sàng dùng chung cho mọi module
career_advisory_service = CareerAdvisoryService()
