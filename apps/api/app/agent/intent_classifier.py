"""
Intent Classifier Module for Conversational Career Guidance Agent.
Combines high-speed rule-based matching with Gemini LLM reasoning.
"""

import re
import logging
from typing import Optional, List, Dict
from .prompts import INTENT_CLASSIFICATION_PROMPT

try:
    from app.modules.graphrag.llm_service import call_gemini_chat
except ImportError:
    try:
        from ..modules.graphrag.llm_service import call_gemini_chat
    except ImportError:
        from llm_service import call_gemini_chat

logger = logging.getLogger("graphrag.agent.intent")

VALID_INTENTS = {"RECOMMEND", "COMPARE", "LOOKUP", "CHITCHAT", "OUT_OF_SCOPE"}


def rule_based_intent_check(prompt: str) -> Optional[str]:
    """Phân loại nhanh bằng quy tắc từ khóa để tối ưu độ trễ cho các câu quen thuộc."""
    clean = prompt.strip().lower()

    # 1. Chào hỏi / Cảm ơn cơ bản
    chitchat_patterns = [
        r"^(xin\s+)?chào(\s+(bạn|ad|bot|em|anh|chị))?$",
        r"^(hello|hi|hey)(\s+there)?$",
        r"^cảm\s+ơn(\s+(bạn|ad|bot|nhiều))?$",
        r"^(bạn|em)\s+(là\s+ai|tên\s+gì|có\s+thể\s+làm\s+gì)(\s+vậy|\s+thế)?$",
        r"^giới\s+thiệu(\s+về\s+bản\s+thân)?$"
    ]
    for p in chitchat_patterns:
        if re.search(p, clean):
            return "CHITCHAT"

    # 2. Đề xuất / Tư vấn trường, ngành (RECOMMEND)
    rec_patterns = [
        r"^(tư\s+vấn|gợi\s+ý|đề\s+xuất|chọn\s+trường|tìm\s+trường)",
        r"(tư\s+vấn|gợi\s+ý|đề\s+xuất)\s+(cho\s+em\s+)?(ngành|trường|nguyện\s+vọng)",
        r"nên\s+học\s+trường\s+nào",
        r"học\s+được\s+trường\s+nào"
    ]
    for p in rec_patterns:
        if re.search(p, clean):
            return "RECOMMEND"

    # 3. Tra cứu thông tin cụ thể & Phân tích chuyên sâu 1 ngành/trường/nghề
    lookup_patterns = [
        r"^học\s+phí",
        r"học\s+phí\s+.+\s+là\s+bao\s+nhiêu",
        r"học\s+phí\s+.+\s+thế\s+nào",
        r"^điểm\s+chuẩn",
        r"^chỉ\s+tiêu(\s+tuyển\s+sinh)?\s+",
        r"ở\s+đâu\b",
        r"địa\s+chỉ(\s+của)?\s+",
        r"có\s+ký\s+túc\s+xá\s+không",
        r"(tìm\s+hiểu|thông\s+tin|giới\s+thiệu|phân\s+tích)(\s+chi\s+tiết)?\s+(về\s+)?trường",
        r"(tìm\s+hiểu|thông\s+tin|giới\s+thiệu|phân\s+tích)(\s+chi\s+tiết)?\s+(về\s+)?(ngành|nghề)",
        r"(phân\s+tích|đánh\s+giá)\s+(chi\s+tiết\s+)?(cơ\s+hội\s+xét\s+tuyển|việc\s+làm|khả\s+năng\s+trúng\s+tuyển)",
        r"tiềm\s+năng\s+việc\s+làm",
        r"mức\s+lương\s+tham\s+chiếu",
        r"môi\s+trường\s+học\s+tập",
        r"ngành\s+đào\s+tạo\s+(nổi\s+bật\s+)?của\s+trường",
        r"thông\s+tin\s+chi\s+tiết\s+về\s+trường",
        r"khả\s+năng\s+trúng\s+tuyển\s+ngành"
    ]
    for p in lookup_patterns:
        if re.search(p, clean):
            return "LOOKUP"

    # 4. So sánh rõ rệt
    compare_patterns = [
        r"^so\s+sánh\s+",
        r"nên\s+chọn\s+.+\s+hay\s+",
        r"khác\s+nhau\s+giữa\s+.+\s+và\s+"
    ]
    for p in compare_patterns:
        if re.search(p, clean):
            return "COMPARE"

    # 5. Tư vấn nguyện vọng có điểm số / khối thi / muốn tìm trường
    has_score = bool(re.search(r'\d{1,2}(?:\.\d{1,2})?\s*(?:đ|điểm)', clean))
    has_group = bool(re.search(r'\b[a-d]\d{2}\b', clean))
    has_advise = any(k in clean for k in ["muốn học", "tư vấn", "chọn ngành", "chọn trường", "đỗ được", "nguyện vọng", "thi vào", "được không", "gợi ý trường"])
    if (has_score or has_group) and has_advise:
        return "RECOMMEND"

    return None


async def classify_intent(
    prompt: str,
    recent_messages: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Phân loại ý định của người dùng bằng kết hợp Fast Rules và Google Gemini LLM.
    Trả về 1 trong 5 nhãn: RECOMMEND, COMPARE, LOOKUP, CHITCHAT, OUT_OF_SCOPE.
    """
    fast_check = rule_based_intent_check(prompt)
    if fast_check:
        logger.info(f"Fast rule classified prompt as '{fast_check}': {prompt[:50]}")
        return fast_check

    prompt_formatted = INTENT_CLASSIFICATION_PROMPT.format(user_prompt=prompt)
    messages = [
        {"role": "user", "content": prompt_formatted}
    ]

    try:
        raw_resp = await call_gemini_chat(messages, temperature=0.1, max_tokens=15)
        cleaned = raw_resp.strip().upper().replace(".", "").replace(",", "").replace("\n", " ").split(" ")[0]
        if cleaned in VALID_INTENTS:
            logger.info(f"Gemini classified intent: {cleaned} for query: {prompt[:50]}")
            return cleaned
        else:
            logger.warning(f"Unexpected response from Gemini intent classification: '{raw_resp}', defaulting to RECOMMEND")
            return "RECOMMEND"
    except Exception as e:
        logger.error(f"Error classifying intent via Gemini: {e}, falling back to RECOMMEND", exc_info=True)
        return "RECOMMEND"
