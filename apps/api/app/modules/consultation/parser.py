"""
Intent and Entity Parser for Natural Language Admission Questions.
Extracts: Score, Subject Group, Target City, Hometown (Priority Zone), Budget, Holland Code.
Falls back to logged-in student profile in PostgreSQL when fields are missing.
"""

import re
from typing import Dict, Any, Optional
from app.modules.recommendations.schemas import RecommendationRequest

# Mapping các tỉnh thành thuộc Khu vực 2 / KV1 / KV2-NT theo Quy chế Tuyển sinh
PROVINCE_PRIORITY_MAP = {
    # KV2 (Thị xã, thành phố trực thuộc tỉnh, các tỉnh đồng bằng): cộng 0.25 - 0.5 điểm
    "long an": ("KV2", 0.5),
    "tiền giang": ("KV2", 0.5),
    "bến tre": ("KV2", 0.5),
    "đồng nai": ("KV2", 0.5),
    "bình dương": ("KV2", 0.5),
    "bà rịa": ("KV2", 0.5),
    "vũng tàu": ("KV2", 0.5),
    "vĩnh long": ("KV2", 0.5),
    "trà vinh": ("KV2", 0.5),
    "hậu giang": ("KV2", 0.5),
    "sóc trăng": ("KV2", 0.5),
    "bạc liêu": ("KV2", 0.5),
    "cà mau": ("KV2", 0.5),
    "an giang": ("KV2", 0.5),
    "kiên giang": ("KV2", 0.5),
    "tây ninh": ("KV2", 0.5),
    "bình thuận": ("KV2", 0.5),
    "ninh thuận": ("KV2", 0.5),
    "khánh hòa": ("KV2", 0.5),
    "phú yên": ("KV2", 0.5),
    "bình định": ("KV2", 0.5),
    "quảng ngãi": ("KV2", 0.5),
    "quảng nam": ("KV2", 0.5),
    "thừa thiên huế": ("KV2", 0.5),
    "huế": ("KV2", 0.5),
    "quảng trị": ("KV2", 0.5),
    "quảng bình": ("KV2", 0.5),
    "hà tĩnh": ("KV2", 0.5),
    "nghệ an": ("KV2", 0.5),
    "thanh hóa": ("KV2", 0.5),
    "nam định": ("KV2", 0.5),
    "thái bình": ("KV2", 0.5),
    "hải dương": ("KV2", 0.5),
    "hưng yên": ("KV2", 0.5),
    "vĩnh phúc": ("KV2", 0.5),
    "bắc ninh": ("KV2", 0.5),
    "hải phòng": ("KV2", 0.25),
    
    # KV1 (Vùng sâu, vùng xa, miền núi, hải đảo): cộng 0.75 điểm
    "hà giang": ("KV1", 0.75),
    "cao bằng": ("KV1", 0.75),
    "bắc kạn": ("KV1", 0.75),
    "tuyên quang": ("KV1", 0.75),
    "lào cai": ("KV1", 0.75),
    "yên bái": ("KV1", 0.75),
    "thái nguyên": ("KV1", 0.75),
    "lạng sơn": ("KV1", 0.75),
    "bắc giang": ("KV1", 0.75),
    "phú thọ": ("KV1", 0.75),
    "điện biên": ("KV1", 0.75),
    "lai châu": ("KV1", 0.75),
    "sơn la": ("KV1", 0.75),
    "hòa bình": ("KV1", 0.75),
    "kon tum": ("KV1", 0.75),
    "gia lai": ("KV1", 0.75),
    "đắk lắk": ("KV1", 0.75),
    "đắk nông": ("KV1", 0.75),
    "lâm đồng": ("KV1", 0.75),
}

CITY_ALIASES = {
    "hcm": "TP.HCM",
    "tp.hcm": "TP.HCM",
    "tphcm": "TP.HCM",
    "tp hcm": "TP.HCM",
    "hồ chí minh": "TP.HCM",
    "tp. hồ chí minh": "TP.HCM",
    "sài gòn": "TP.HCM",
    "sai gon": "TP.HCM",
    "hà nội": "Hà Nội",
    "ha noi": "Hà Nội",
    "hn": "Hà Nội",
    "đà nẵng": "Đà Nẵng",
    "da nang": "Đà Nẵng",
    "cần thơ": "Cần Thơ",
}


def parse_intent_and_entities(query_text: str, profile_defaults: Optional[Dict[str, Any]] = None) -> RecommendationRequest:
    """
    Trích xuất thực thể từ câu hỏi tự nhiên:
    Ví dụ: 'tôi 25 điểm A01 ở Long an muốn học ở đại học ở HCM với kinh phí 100triệu'
    -> student_score = 25.0
    -> student_group_code = 'A01'
    -> preferred_city = 'TP.HCM'
    -> bonus_points = 0.5 (Khu vực 2 - Long An)
    -> max_annual_budget = 100,000,000
    -> holland_code = 'RIA' (hoặc từ profile)
    """
    text_lower = query_text.lower()
    defaults = profile_defaults or {}

    # 1. Trích xuất Điểm số (Score)
    score = defaults.get("student_score")
    score_match = re.search(r'(\d{1,2}(?:[\.,]\d{1,2})?)\s*(?:điểm|đ\b)', text_lower)
    if not score_match:
        score_match = re.search(r'(?:được|tầm|khoảng|thi|đạt)\s*(\d{1,2}(?:[\.,]\d{1,2})?)', text_lower)
    if score_match:
        try:
            score = float(score_match.group(1).replace(",", "."))
        except ValueError:
            pass
    if score is None:
        score = 25.0  # Mức trung bình chuẩn

    # 2. Trích xuất Khối thi (Subject Group)
    group = defaults.get("student_group_code")
    group_match = re.search(r'\b([a-d]\d{2})\b', text_lower)
    if group_match:
        group = group_match.group(1).upper()
    if not group:
        group = "A01" if "tiếng anh" in text_lower or "anh" in text_lower else "A00"

    # 3. Trích xuất Khu vực mong muốn học (Target City)
    city = defaults.get("preferred_city")
    for alias, standard_city in CITY_ALIASES.items():
        if alias in text_lower:
            city = standard_city
            break

    # 4. Trích xuất Quê quán / Khu vực ưu tiên (Hometown & Priority points)
    bonus_points = defaults.get("bonus_points", 0.0)
    for prov, (zone, pts) in PROVINCE_PRIORITY_MAP.items():
        # Kiểm tra quê quán (VD: 'ở long an', 'quê long an', 'tại long an')
        if prov in text_lower:
            bonus_points = pts
            break

    # Kiểm tra trực tiếp từ khóa KV
    if "kv1" in text_lower or "khu vực 1" in text_lower:
        bonus_points = 0.75
    elif "kv2-nt" in text_lower or "khu vực 2-nt" in text_lower or "nông thôn" in text_lower:
        bonus_points = 0.5
    elif "kv2" in text_lower or "khu vực 2" in text_lower:
        bonus_points = 0.25

    # 5. Trích xuất Ngân sách học phí (Budget)
    budget = defaults.get("max_annual_budget")
    budget_match = re.search(r'(\d+)\s*(?:triệu|tr\b|củ|m\b)', text_lower)
    if budget_match:
        try:
            budget = int(budget_match.group(1)) * 1_000_000
        except ValueError:
            pass
    else:
        # Kiểm tra dạng số đầy đủ: 100000000 hoặc 100.000.000
        num_match = re.search(r'(\d{1,3}(?:[\.,]\d{3}){2,})', text_lower)
        if num_match:
            try:
                budget = int(re.sub(r'[\.,]', '', num_match.group(1)))
            except ValueError:
                pass
    if not budget or budget <= 0:
        budget = 50_000_000  # Ngân sách mặc định phổ biến

    # 6. Mã Holland RIASEC
    holland = defaults.get("holland_code", "RIA")
    holland_match = re.search(r'\b([riasec]{3})\b', text_lower)
    if holland_match:
        holland = holland_match.group(1).upper()

    return RecommendationRequest(
        target_year=2025,
        student_method="Thi THPT",
        student_group_code=group,
        student_score=score,
        bonus_points=bonus_points,
        max_annual_budget=budget,
        student_gender=defaults.get("student_gender", "Male"),
        student_height=defaults.get("student_height"),
        student_eye_degree=defaults.get("student_eye_degree"),
        preferred_city=city,
        holland_code=holland,
    )

