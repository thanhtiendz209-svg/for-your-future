"""
LLM Consultation Service with Zero-Hallucination Prompting and Server-Sent Events (SSE).
Integrates exclusively with Google Gemini API (gemini-flash-lite-latest / gemini-2.5-flash)
via OpenAI-compatible streaming protocol with grounded fallback streaming.
"""

import os
import json
import asyncio
import logging
from typing import AsyncGenerator, List, Optional, Dict, Any
import httpx
from app.core.config import settings

try:
    from .models.recommendation import (
        RecommendationResultItem,
        ScoredProgramItem,
        PortfolioRecommendationResponse
    )
except ImportError:
    from models.recommendation import (
        RecommendationResultItem,
        ScoredProgramItem,
        PortfolioRecommendationResponse
    )

logger = logging.getLogger("graphrag.llm")

# Google Gemini API Exclusive Configuration
GEMINI_API_KEY: str = settings.GEMINI_API_KEY
GEMINI_MODEL: str = settings.GEMINI_MODEL
GEMINI_OPENAI_URL: str = settings.GEMINI_OPENAI_BASE_URL.rstrip("/") + "/chat/completions"


class GeminiStreamInterrupted(Exception):
    """Gemini ended before delivering a complete response."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def with_continuation(
    messages: List[Dict[str, str]], continuation: Optional[str]
) -> List[Dict[str, str]]:
    if not continuation:
        return messages
    return [
        *messages,
        {"role": "assistant", "content": continuation},
        {"role": "user", "content": "Viết tiếp từ chỗ đang dở. Chỉ bổ sung phần còn thiếu."},
    ]


async def _gemini_sse(client, url, headers, body, *, native=False) -> AsyncGenerator[str, None]:
    has_text = False
    finished = False
    try:
        async with client.stream("POST", url, headers=headers, json=body) as response:
            if response.status_code in (429, 503):
                logger.warning("Gemini streaming HTTP %s", response.status_code)
                raise GeminiStreamInterrupted("busy")
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if not payload:
                    continue
                if payload == "[DONE]":
                    finished = True
                    break
                data = json.loads(payload)
                if error := data.get("error"):
                    reason = "busy" if error.get("code") in (429, 503) else "connection"
                    raise GeminiStreamInterrupted(reason)
                if native:
                    if (data.get("promptFeedback") or {}).get("blockReason"):
                        raise GeminiStreamInterrupted("blocked")
                    candidates = data.get("candidates") or []
                    if not candidates:
                        continue
                    candidate = candidates[0]
                    parts = (candidate.get("content") or {}).get("parts") or []
                    text = "".join(part.get("text", "") for part in parts if not part.get("thought"))
                    finish = candidate.get("finishReason")
                else:
                    choices = data.get("choices") or []
                    if not choices:
                        continue
                    choice = choices[0]
                    text = (choice.get("delta") or {}).get("content") or ""
                    finish = choice.get("finish_reason")
                if text:
                    has_text = has_text or bool(text.strip())
                    yield text
                if finish in ("length", "MAX_TOKENS"):
                    raise GeminiStreamInterrupted("length")
                if finish in ("stop", "STOP"):
                    finished = True
                    break
                if finish in ("content_filter", "SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII"):
                    raise GeminiStreamInterrupted("blocked")
                if finish and finish != "FINISH_REASON_UNSPECIFIED":
                    raise GeminiStreamInterrupted("connection")
    except (httpx.HTTPError, json.JSONDecodeError) as error:
        logger.warning("Gemini stream ended (%s)", type(error).__name__)
        raise GeminiStreamInterrupted("connection") from error

    if not finished or not has_text:
        raise GeminiStreamInterrupted("connection")


async def stream_gemini_messages(
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 1500
) -> AsyncGenerator[str, None]:
    """Yield Gemini text as it arrives, switching APIs only before visible text."""
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
    body = {
        "model": GEMINI_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    has_text = False
    async with httpx.AsyncClient(timeout=httpx.Timeout(25.0, connect=8.0)) as client:
        try:
            async for text in _gemini_sse(client, GEMINI_OPENAI_URL, headers, body):
                has_text = has_text or bool(text.strip())
                yield text
            return
        except GeminiStreamInterrupted as error:
            if has_text or error.reason not in ("connection", "busy"):
                raise

        native_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:streamGenerateContent?alt=sse"
        native_body = {
            "contents": [
                {
                    "role": "model" if message["role"] == "assistant" else "user",
                    "parts": [{"text": message["content"]}],
                }
                for message in messages if message["role"] != "system"
            ],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        system = "\n".join(message["content"] for message in messages if message["role"] == "system")
        if system:
            native_body["systemInstruction"] = {"parts": [{"text": system}]}
        logger.info("Using Gemini native streaming fallback")
        async for text in _gemini_sse(
            client, native_url, {"x-goog-api-key": GEMINI_API_KEY}, native_body, native=True
        ):
            yield text


async def call_gemini_native(prompt_text: str, max_tokens: int = 800) -> str:
    """Gọi native Google Gemini generateContent API nếu OpenAI endpoint quá tải (503/429)."""
    native_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": max_tokens
        }
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(native_url, headers={"x-goog-api-key": GEMINI_API_KEY}, json=payload)
            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
    except Exception as e:
        logger.warning(f"Native Gemini fallback error: {e}")
    return ""


async def call_gemini_chat(
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 800
) -> str:
    """Gọi Gemini API với cơ chế tự động thử lại (Retry) và Native Fallback khi quá tải."""
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": GEMINI_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }

    # Thử qua OpenAI-compatible endpoint
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(GEMINI_OPENAI_URL, headers=headers, json=body)
                if res.status_code == 200:
                    d = res.json()
                    choices = d.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
                elif res.status_code in (503, 429):
                    logger.warning(f"Gemini returned {res.status_code} (attempt {attempt+1}), pausing before retry/fallback")
                    await asyncio.sleep(0.8)
                else:
                    logger.warning(f"Gemini call error {res.status_code}: {res.text[:200]}")
                    break
        except Exception as e:
            logger.warning(f"Error calling Gemini OpenAI endpoint (attempt {attempt+1}): {e}")
            await asyncio.sleep(0.5)

    # Nếu OpenAI endpoint bị nghẽn (503), chuyển hướng sang Native endpoint
    combined_prompt = "\n".join(m.get("content", "") for m in messages)
    native_resp = await call_gemini_native(combined_prompt, max_tokens=max_tokens)
    if native_resp:
        return native_resp

    return ""


def build_portfolio_system_prompt(
    portfolio: Any,
    user_prompt: str,
    slots: Optional[Dict[str, Any]] = None
) -> str:
    """
    Xây dựng System Prompt chiến lược phân tầng danh mục nguyện vọng (Reach - Target - Safe)
    kết hợp dữ liệu thực chứng từ Knowledge Graph và việc làm thực tế cào từ CareerViet.
    Chấp nhận linh hoạt cả đối tượng PortfolioRecommendationResponse lẫn portfolio_dict.
    """
    def format_card(idx: int, item: Any) -> str:
        if isinstance(item, dict):
            prog = item.get("program_name", "")
            uni = item.get("university_name", "")
            loc = item.get("location") or item.get("city", "Toàn quốc")
            bench = item.get("admission_score") or item.get("benchmark_score", 0.0)
            margin = item.get("score_margin", 0.0)
            tuition = item.get("tuition_fee")
            if tuition is not None:
                tuition_str = f"{tuition} triệu VND/năm"
            else:
                actual_t = item.get("actual_tuition") or item.get("official_tuition")
                tuition_str = f"{actual_t:,.0f} VND/năm" if actual_t else "Theo quy định nhà nước"

            careers = ", ".join(item.get("career_connections", [])) or item.get("career_name") or "Chuyên môn cao"
            hiring = ", ".join(item.get("hiring_partners", [])) or ", ".join(item.get("hiring_companies", [])) or "Các tập đoàn lớn"
            mcdm = item.get("mcdm_rank_score") or item.get("mcdm_score", 0.0)
            return (
                f"  {idx}. {prog} - {uni} ({loc})\n"
                f"     - Điểm chuẩn tham chiếu: {bench} | Điểm dôi dư: {margin:+.2f} điểm\n"
                f"     - Học phí tham khảo: {tuition_str}\n"
                f"     - Nghề nghiệp: {careers}\n"
                f"     - Doanh nghiệp tuyển dụng tiêu biểu: {hiring}\n"
                f"     - Điểm tổng hợp đa tiêu chí MCDM: {mcdm * 100:.1f}%\n"
            )
        else:
            hiring = ", ".join(getattr(item, "hiring_companies", [])) if getattr(item, "hiring_companies", None) else "Các doanh nghiệp công nghệ lớn"
            actual_t = getattr(item, "actual_tuition", None) or getattr(item, "official_tuition", None)
            tuition_str = f"{actual_t:,.0f} VND/năm" if actual_t else "Theo quy định nhà nước"
            return (
                f"  {idx}. {item.program_name} - {item.university_name} ({getattr(item, 'city', 'Toàn quốc')})\n"
                f"     - Điểm chuẩn tham chiếu: {item.benchmark_score} | Điểm dôi dư: +{item.score_margin:.2f} điểm\n"
                f"     - Học phí thực tế: {tuition_str}\n"
                f"     - Nghề nghiệp: {getattr(item, 'career_name', '')} (Tăng trưởng: +{getattr(item, 'job_growth_rate', 0)}%)\n"
                f"     - Doanh nghiệp tuyển dụng tiêu biểu (CareerViet): {hiring}\n"
                f"     - Điểm tổng hợp đa tiêu chí MCDM: {item.mcdm_score * 100:.1f}%\n"
            )

    reach_list = []
    target_list = []
    safe_list = []

    if isinstance(portfolio, dict):
        reach_list = portfolio.get("reach") or portfolio.get("reach_programs") or []
        target_list = portfolio.get("target") or portfolio.get("target_programs") or []
        safe_list = portfolio.get("safe") or portfolio.get("safe_programs") or []
    elif portfolio is not None:
        reach_list = getattr(portfolio, "reach_programs", None) or getattr(portfolio, "reach", []) or []
        target_list = getattr(portfolio, "target_programs", None) or getattr(portfolio, "target", []) or []
        safe_list = getattr(portfolio, "safe_programs", None) or getattr(portfolio, "safe", []) or []

    reach_text = "\n".join(format_card(i, p) for i, p in enumerate(reach_list, 1)) or "  Không có ngành mạo hiểm phù hợp."
    target_text = "\n".join(format_card(i, p) for i, p in enumerate(target_list, 1)) or "  Không có ngành vừa sức phù hợp."
    safe_text = "\n".join(format_card(i, p) for i, p in enumerate(safe_list, 1)) or "  Không có ngành an toàn phù hợp."

    # Thông tin intent thực tế từ học sinh
    score_val = None
    group_val = None
    budget_val = None
    holland_val = None
    city_val = None

    if slots:
        score_val = slots.get("student_score")
        group_val = slots.get("student_group_code")
        budget_val = slots.get("max_annual_budget")
        holland_val = slots.get("inferred_holland_code")
        city_val = slots.get("preferred_city")
    elif portfolio and hasattr(portfolio, "extracted_intent") and portfolio.extracted_intent:
        intent = portfolio.extracted_intent
        score_val = intent.student_score
        group_val = intent.student_group_code
        budget_val = intent.max_annual_budget
        holland_val = intent.inferred_holland_code
        city_val = intent.preferred_city

    score = f"{score_val:.2f} điểm" if score_val is not None else "Chưa cung cấp điểm cụ thể"
    group = group_val if group_val else "Các khối thi phù hợp"
    budget_str = f"{budget_val:,.0f} VND/năm (~{round(budget_val / 1_000_000)} triệu VND/năm)" if budget_val else "Tiêu chuẩn đại học công lập (~20 - 26 triệu VND/năm)"
    holland = holland_val if holland_val else "Đề xuất theo điểm số & tổ hợp (chưa xác định mã Holland)"
    city = city_val if city_val else "Toàn quốc"

    tech_keywords = slots.get("target_major_keywords", []) if slots else []
    kw_str = ", ".join(tech_keywords) if tech_keywords else "Công nghệ thông tin, Kỹ thuật, Khoa học máy tính"

    prompt = (
        "Bạn là Chuyên gia Cố vấn Hướng nghiệp và Tuyển sinh Đại học cấp cao của Hệ thống GraphRAG.\n\n"
        "=== QUY TẮC BẮT BUỘC (ZERO-HALLUCINATION POLICY) ===\n"
        "1. TUYỆT ĐỐI KHÔNG BỊA ĐẶT điểm chuẩn, trường ngành, học phí nằm ngoài DỮ LIỆU ĐÃ XÁC THỰC bên dưới.\n"
        "2. Toàn bộ tư vấn phải dựa trên các con số thực tế: Biên độ dôi dư, Học phí, Độ khớp Holland, và Doanh nghiệp tuyển dụng.\n"
        "3. Lời văn: Khách quan, thấu hiểu, mang tính chiến lược định hướng tương lai vững chắc cho người có tư duy logic/kỹ thuật.\n"
        "4. Bám sát các ngành trong 3 danh mục đã cung cấp bên dưới (Reach, Target, Safe). Tuyệt đối không đề xuất ngành ngoài danh mục.\n\n"
        "=== DỮ LIỆU ĐÃ TRÍCH XUẤT TỪ GRAPH THEO THUẬT TOÁN RANKING MCDM ===\n"
        f"- Học sinh: Điểm={score}, Khối={group}, Ngân sách tối đa={budget_str}\n"
        f"- Mã tính cách Holland suy luận: {holland}\n"
        f"- Định hướng ngành nghề: {kw_str}\n"
        f"- Thành phố ưu tiên: {city}\n\n"
        "[DANH MỤC 1: NGUYỆN VỌNG MẠO HIỂM / MƠ ƯỚC (REACH)]\n"
        f"{reach_text}\n\n"
        "[DANH MỤC 2: NGUYỆN VỌNG VỪA SỨC / MỤC TIÊU TRỌNG TÂM (TARGET)]\n"
        f"{target_text}\n\n"
        "[DANH MỤC 3: NGUYỆN VỌNG AN TOÀN CAO / CHẮC ĂN (SAFE)]\n"
        f"{safe_text}\n\n"
        "=== CÂU HỎI CỦA HỌC SINH ===\n"
        f"\"{user_prompt}\"\n\n"
        "=== CẤU TRÚC PHẢN HỒI YÊU CẦU ===\n"
        "1. Chào học sinh, ghi nhận năng lực điểm số và xu hướng tính cách nghề nghiệp.\n"
        "2. Chiến lược sắp xếp danh mục nguyện vọng (NV1 Reach, NV2-NV3 Target, NV4 Safe).\n"
        "3. Phân tích thị trường lao động thực tế (nhu cầu việc làm, mức lương tham chiếu CareerViet, kỹ năng cần chuẩn bị).\n"
        "4. Lời chúc và động lực tự tin chinh phục kỳ thi.\n\n"
        "Bắt đầu tư vấn bằng tiếng Việt:"
    )
    return prompt


def _fallback_portfolio_text(
    portfolio: Any, slots: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Bộ sinh Grounded In-Context cục bộ nếu mất mạng hoàn toàn"""
    score = 25.0
    group = "A00"
    if slots:
        score = slots.get("student_score", score)
        group = slots.get("student_group_code", group)
    elif portfolio and hasattr(portfolio, "extracted_intent") and portfolio.extracted_intent:
        score = portfolio.extracted_intent.student_score
        group = portfolio.extracted_intent.student_group_code

    reach_list = (portfolio.get("reach") or portfolio.get("reach_programs") or []) if isinstance(portfolio, dict) else (getattr(portfolio, "reach_programs", []) or [])
    target_list = (portfolio.get("target") or portfolio.get("target_programs") or []) if isinstance(portfolio, dict) else (getattr(portfolio, "target_programs", []) or [])
    safe_list = (portfolio.get("safe") or portfolio.get("safe_programs") or []) if isinstance(portfolio, dict) else (getattr(portfolio, "safe_programs", []) or [])

    lines = [
        f"Chào bạn! Dựa trên phân tích từ Knowledge Graph và điểm số {score} khối {group}:\n\n",
        "### 🎯 Phân bổ Chiến lược Nguyện vọng 3 Tầng:\n"
    ]

    def _get_name_and_margin(p):
        if isinstance(p, dict):
            return p.get("program_name"), p.get("university_name"), p.get("admission_score", p.get("benchmark_score")), p.get("score_margin", 0.0)
        return p.program_name, p.university_name, p.benchmark_score, getattr(p, "score_margin", 0.0)

    if reach_list:
        lines.append("\n**1. Danh mục Mạo hiểm / Mơ ước (Reach):**\n")
        for p in reach_list:
            prog, uni, bench, margin = _get_name_and_margin(p)
            lines.append(f"- **{prog}** - {uni} (Điểm chuẩn: {bench}, chênh lệch: {margin:+.2f} điểm)\n")

    if target_list:
        lines.append("\n**2. Danh mục Vừa sức / Trọng tâm (Target):**\n")
        for p in target_list:
            prog, uni, bench, margin = _get_name_and_margin(p)
            lines.append(f"- **{prog}** - {uni} (Điểm chuẩn: {bench}, chênh lệch: {margin:+.2f} điểm)\n")

    if safe_list:
        lines.append("\n**3. Danh mục An toàn / Dự phòng (Safe):**\n")
        for p in safe_list:
            prog, uni, bench, margin = _get_name_and_margin(p)
            lines.append(f"- **{prog}** - {uni} (Điểm chuẩn: {bench}, an toàn: +{margin:.2f} điểm)\n")

    lines.append("\nChúc bạn đưa ra quyết định sáng suốt và đạt kết quả cao nhất!")

    return lines


async def stream_portfolio_tokens(
    portfolio: Any,
    user_prompt: str,
    slots: Optional[Dict[str, Any]] = None,
    continuation: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    prompt = build_portfolio_system_prompt(portfolio, user_prompt, slots=slots)
    messages = [
        {"role": "system", "content": "Bạn là chuyên gia tư vấn tuyển sinh đại học cấp cao, phản hồi mạch lạc bằng tiếng Việt."},
        {"role": "user", "content": prompt},
    ]
    has_text = False
    try:
        async for token in stream_gemini_messages(with_continuation(messages, continuation), temperature=0.3):
            has_text = has_text or bool(token.strip())
            yield token
    except GeminiStreamInterrupted as error:
        if has_text or continuation or error.reason not in ("connection", "busy"):
            raise
        for line in _fallback_portfolio_text(portfolio, slots):
            yield line


async def stream_portfolio_ai_consultation(
    portfolio: Any,
    user_prompt: str,
    slots: Optional[Dict[str, Any]] = None,
) -> AsyncGenerator[str, None]:
    """Compatibility adapter for callers that consume SSE-formatted tokens."""
    try:
        async for token in stream_portfolio_tokens(portfolio, user_prompt, slots):
            yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
    except GeminiStreamInterrupted as error:
        yield f"data: {json.dumps({'type': 'interrupted', 'reason': error.reason})}\n\n"
        return
    yield "data: [DONE]\n\n"


async def stream_ai_consultation(
    query_text: str,
    context_items: List[RecommendationResultItem]
) -> AsyncGenerator[str, None]:
    """Hàm tương thích ngược cho endpoint cũ /api/v1/consult/stream"""
    from .recommender import rank_and_score_programs, build_portfolio_recommendations
    from .query_parser import parse_student_prompt

    intent = parse_student_prompt(query_text)
    scored = rank_and_score_programs(context_items, intent)
    portfolio = build_portfolio_recommendations(scored, intent)
    async for chunk in stream_portfolio_ai_consultation(portfolio, query_text):
        yield chunk
