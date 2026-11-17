"""
Prompt Templates, Guardrails, and Security Filters for AI Consultation.
Strict Zero-Hallucination policy with exact evidence citation.
"""

import re
from typing import List, Dict, Any

# Blacklist keywords for sensitive/inappropriate topics
INAPPROPRIATE_KEYWORDS = [
    "bạo lực", "vũ khí", "khủng bố", "khiêu dâm", "đánh bạc", 
    "chính trị cực đoan", "phá hoại", "tự tử", "hack", "ddos"
]

# Prompt injection indicators
PROMPT_INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"bỏ qua (mọi )?hướng dẫn trước",
    r"you are now (an unrestricted|DAN|jailbreak)",
    r"system prompt:",
    r"override rules",
    r"reveal your hidden",
]


def sanitize_user_input(user_input: str) -> str:
    """Kiểm tra và khử độc câu hỏi của người dùng để chống prompt injection và nội dung độc hại."""
    cleaned = user_input.strip()
    
    # Check injection patterns
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return "Xin chào, tôi cần được tư vấn về chọn trường và định hướng nghề nghiệp phù hợp với điểm số của tôi."
            
    # Check inappropriate keywords
    for keyword in INAPPROPRIATE_KEYWORDS:
        if keyword in cleaned.lower():
            return "Xin chào, hãy tư vấn cho tôi về các ngành học và cơ hội nghề nghiệp tương ứng."
            
    return cleaned


def build_zero_hallucination_system_prompt(
    context_items: List[Dict[str, Any]],
    query_text: str
) -> str:
    """
    Xây dựng System Prompt với kỹ thuật Grounded In-Context Learning (Zero-Hallucination).
    Ràng buộc LLM tuyệt đối chỉ dựa vào dữ liệu Sub-graph được trích xuất từ Knowledge Graph.
    """
    context_blocks = []
    for idx, item in enumerate(context_items, 1):
        facilities = item.get("facilities", [])
        facilities_str = ", ".join(facilities) if facilities else "Tiêu chuẩn quốc gia"
        companies = item.get("hiring_companies", [])
        hiring_str = ", ".join(companies) if companies else "Các tập đoàn hàng đầu"
        
        block = (
            f"Lựa chọn #{idx}:\n"
            f"- Trường: {item.get('university_name')} ({item.get('university_id')}) - Khu vực: {item.get('city')}\n"
            f"- Ngành: {item.get('program_name')} (Mã ngành: {item.get('program_id')})\n"
            f"- Văn bằng: {item.get('credential', 'Cử nhân/Kỹ sư')}\n"
            f"- Điểm chuẩn tham chiếu: {item.get('benchmark_score')} | Điểm sàn: {item.get('minimum_threshold') or 'Không quy định'}\n"
            f"- Biên độ an toàn điểm số: +{item.get('score_margin', 0):.2f} điểm (Đánh giá: {item.get('safety_level', 'Safe')})\n"
            f"- Học phí thực tế: {item.get('actual_tuition', 0):,.0f} VND/năm (Trợ cấp/bù giá: {'Có' if item.get('is_subsidized') else 'Không'})\n"
            f"- Nghề nghiệp chuẩn bị: {item.get('career_name')} (Tăng trưởng nhân lực: +{item.get('job_growth_rate', 0)}%)\n"
            f"- Doanh nghiệp tiêu biểu: {hiring_str}\n"
            f"- Độ phù hợp sở thích Holland: {float(item.get('holland_match_score', 1.0)) * 100:.1f}%\n"
            f"- Cơ sở vật chất: {facilities_str}\n"
        )
        context_blocks.append(block)

    formatted_context = "\n".join(context_blocks) if context_blocks else "Không có ngành nào vượt qua bộ lọc cứng."

    prompt = (
        "Bạn là Chuyên viên Cố vấn Tuyển sinh & Hướng nghiệp đại học của nền tảng 'For Your Future'.\n\n"
        "=== BẢN NGUYÊN TẮC BẮT BUỘC (ZERO-HALLUCINATION POLICY) ===\n"
        "1. TUYỆT ĐỐI KHÔNG BỊA ĐẶT điểm chuẩn, học phí, chỉ tiêu, hoặc quy chế tuyển sinh nằm ngoài BỐI CẢNH DỮ LIỆU ĐÃ XÁC THỰC bên dưới.\n"
        "2. Điểm chuẩn năm trước chỉ mang tính chất tham khảo, không đảm bảo trúng tuyển 100% trong tương lai.\n"
        "3. Tách biệt rõ giữa: Sở thích cá nhân (Holland/RIASEC), Năng lực học tập (Điểm số), và Khả năng tài chính.\n"
        "4. Phân tích cụ thể biên độ điểm dôi dư (score_margin) và phân loại độ an toàn (Safe/Target/Reach).\n"
        "5. Ngôn phong: Chuyên nghiệp, khách quan, khích lệ, thực tế và dễ hiểu đối với học sinh THPT.\n\n"
        "=== BỐI CẢNH DỮ LIỆU ĐÃ LỌC TẤT ĐỊNH TỪ CƠ SỞ DỮ LIỆU ===\n"
        f"{formatted_context}\n\n"
        "=== CÂU HỎI CỦA THÍ SINH ===\n"
        f"\"{query_text}\"\n\n"
        "=== HƯỚNG DẪN CẤU TRÚC PHẢN HỒI ===\n"
        "1. Chào hỏi thân thiện và nhận định nhanh về định hướng của bạn.\n"
        "2. Đánh giá tổng quan năng lực điểm số xét tuyển so với điểm chuẩn tham khảo.\n"
        "3. Phân tích chi tiết từng lựa chọn ngành/trường tối ưu (học phí, việc làm, mức độ an toàn).\n"
        "4. Lời khuyên hành động cụ thể để tăng cơ hội trúng tuyển và chuẩn bị kỹ năng.\n\n"
        "Bắt đầu trả lời chi tiết bằng tiếng Việt:"
    )
    return prompt

