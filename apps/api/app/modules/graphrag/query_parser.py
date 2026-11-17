"""
Query Parser & Intent Decomposition Engine for Vietnamese Educational & Career Guidance.
Extracts structured constraint slots and infers RIASEC Holland codes from free-form student prompts.
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple
try:
    from .models.recommendation import ExtractedIntent
except ImportError:
    from models.recommendation import ExtractedIntent

# Bảng từ khóa ánh xạ tính cách & sở thích sang 6 nhóm Holland RIASEC
HOLLAND_KEYWORD_MAP: Dict[str, List[str]] = {
    "R": [
        "mày mò", "thực hành", "máy tính", "phần cứng", "cơ khí", "kỹ thuật", "sửa chữa",
        "lắp ráp", "điện tử", "chế tạo", "công cụ", "độc lập", "máy móc", "công nghệ", "robot"
    ],
    "I": [
        "tư duy", "logic", "nghiên cứu", "khoa học", "phân tích", "dữ liệu", "giải thuật",
        "toán", "tìm hiểu", "khám phá", "thuật toán", "trí tuệ", "thông minh", "chuyên sâu"
    ],
    "A": [
        "sáng tạo", "nghệ thuật", "thiết kế", "vẽ", "thẩm mỹ", "đồ họa", "nội dung",
        "ý tưởng", "hình ảnh", "video", "truyền thông", "viết lách", "âm nhạc", "thời trang"
    ],
    "S": [
        "giúp đỡ", "giao tiếp", "tâm lý", "giảng dạy", "sư phạm", "hướng dẫn", "chăm sóc",
        "cộng đồng", "lắng nghe", "tư vấn", "kết nối", "xã hội", "bác sĩ", "y tá", "điều dưỡng"
    ],
    "E": [
        "kinh doanh", "bán hàng", "khởi nghiệp", "lãnh đạo", "quản lý", "quản trị", "đàm phán",
        "thuyết phục", "marketing", "đầu tư", "thương mại", "thị trường", "tiên phong"
    ],
    "C": [
        "số liệu", "kế toán", "tài chính", "ngân hàng", "kiểm toán", "quy trình", "ngăn nắp",
        "chi tiết", "cẩn thận", "hồ sơ", "chính xác", "luật", "thủ tục", "quản trị văn phòng"
    ]
}

# Danh mục khối thi chuẩn quốc gia
STANDARD_SUBJECT_GROUPS = [
    "A00", "A01", "A02", "B00", "B08", "C00", "C01", "D01", "D07", "D08", "D14", "D15", "H00", "V00"
]

# Chuẩn hóa tên thành phố / tỉnh
CITY_SYNONYMS: Dict[str, str] = {
    "hồ chí minh": "Hồ Chí Minh",
    "tphcm": "Hồ Chí Minh",
    "tp hcm": "Hồ Chí Minh",
    "tp.hcm": "Hồ Chí Minh",
    "sài gòn": "Hồ Chí Minh",
    "sg": "Hồ Chí Minh",
    "hà nội": "Hà Nội",
    "hn": "Hà Nội",
    "đà nẵng": "Đà Nẵng",
    "đn": "Đà Nẵng",
    "cần thơ": "Cần Thơ",
    "hải phòng": "Hải Phòng",
    "bình dương": "Bình Dương",
    "đồng nai": "Đồng Nai",
    "thừa thiên huế": "Huế",
    "huế": "Huế",
}


def normalize_vietnamese_text(text: str) -> str:
    """Chuẩn hóa Unicode NFC và chữ thường"""
    return unicodedata.normalize("NFC", text.strip().lower())


def extract_student_score(text: str) -> Optional[float]:
    """Bóc tách điểm thi của học sinh (Thang 30 hoặc thang ĐGNL 1200)"""
    # Pattern 1: '26.5 điểm', '26,5đ', 'đạt 27 điểm', 'được 25.0'
    patterns = [
        r'(?:được|đạt|thi|tổng)?\s*(\d{1,2}(?:[\.,]\d{1,2})?)\s*(?:điểm|đ\b)',
        r'(?:điểm|đạt)\s*(?:là\s*)?(\d{1,2}(?:[\.,]\d{1,2})?)',
        r'(\d{3,4})\s*(?:điểm\s*)?(?:đgnl|đánh giá năng lực)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val_str = m.group(1).replace(",", ".")
            try:
                val = float(val_str)
                if 0.0 <= val <= 1200.0:
                    return val
            except ValueError:
                pass
    return None


def extract_group_code(text: str) -> Optional[str]:
    """Bóc tách khối thi xét tuyển (A00, A01, D01, B00...)"""
    match = re.search(r'\b(khối\s+)?([A-D]\d{2}|[H|V]\d{2})\b', text, re.IGNORECASE)
    if match:
        code = match.group(2).upper()
        if code in STANDARD_SUBJECT_GROUPS:
            return code
    return None


def extract_budget(text: str) -> Optional[int]:
    """Bóc tách mức ngân sách học phí tối đa (VND)"""
    # Pattern: 30-40 triệu, 40 củ, 35tr, 50.000.000đ
    m = re.search(r'(\d+(?:[\.,]\d+)?)\s*(?:-\s*(\d+(?:[\.,]\d+)?)\s*)?(triệu|tr|củ|trđ)', text, re.IGNORECASE)
    if m:
        # Nếu có dải (VD 30-40 triệu), lấy cận trên (40 triệu)
        num_str = m.group(2) if m.group(2) else m.group(1)
        num = float(num_str.replace(",", "."))
        return int(num * 1_000_000)
    
    # Pattern số cụ thể (VD 40000000 hoặc 40.000.000)
    m_num = re.search(r'(\d{1,3}(?:[\.,]\d{3}){2})\s*(?:vnd|đ|đồng)?', text, re.IGNORECASE)
    if m_num:
        clean = re.sub(r'[\.,]', '', m_num.group(1))
        return int(clean)

    return None


def extract_city(text: str) -> Optional[str]:
    """Bóc tách thành phố / địa phương ưu tiên"""
    norm = normalize_vietnamese_text(text)
    for synonym, canonical in CITY_SYNONYMS.items():
        if re.search(r'\b' + re.escape(synonym) + r'\b', norm):
            return canonical
    return None


def extract_physical_traits(text: str) -> Tuple[Optional[float], Optional[float], str]:
    """Bóc tách chiều cao (cm), độ cận thị (đi-ốp) và giới tính"""
    height: Optional[float] = None
    eye_degree: Optional[float] = None
    gender: str = "Any"

    # Chiều cao: 1m70, 1.7m, 168cm
    m_h = re.search(r'(\d(?:m|\.)\d{2})\b|(\d{3})\s*cm\b', text, re.IGNORECASE)
    if m_h:
        if m_h.group(1):
            val = float(m_h.group(1).replace("m", "."))
            height = val * 100.0
        elif m_h.group(2):
            height = float(m_h.group(2))

    # Độ cận: cận 2.5 độ, cận 3 đi ốp
    m_eye = re.search(r'cận\s*(\d+(?:[\.,]\d+)?)\s*(?:độ|đi-ốp|diop)', text, re.IGNORECASE)
    if m_eye:
        eye_degree = float(m_eye.group(1).replace(",", "."))

    # Giới tính
    if re.search(r'\b(nam|con trai|em là nam)\b', text, re.IGNORECASE):
        gender = "Male"
    elif re.search(r'\b(nữ|con gái|em là nữ)\b', text, re.IGNORECASE):
        gender = "Female"

    return height, eye_degree, gender


def infer_holland_code(text: str) -> str:
    """Suy luận mã 3 ký tự Holland RIASEC từ phân tích tần suất từ khóa"""
    norm = normalize_vietnamese_text(text)
    scores: Dict[str, int] = {k: 0 for k in HOLLAND_KEYWORD_MAP.keys()}

    for dimension, keywords in HOLLAND_KEYWORD_MAP.items():
        for kw in keywords:
            if kw in norm:
                scores[dimension] += 1

    # Sắp xếp giảm dần theo điểm số
    sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_3 = [dim for dim, count in sorted_dims[:3]]

    # Nếu không có từ khóa nào khớp, fallback sang nhóm 'RIA' (phù hợp kỹ thuật/công nghệ/phân tích)
    if scores[sorted_dims[0][0]] == 0:
        return "RIA"

    # Đảm bảo đủ 3 chữ cái
    res = "".join(top_3)
    for char in "RIASEC":
        if len(res) >= 3:
            break
        if char not in res:
            res += char
    return res[:3]


def extract_career_keywords(text: str) -> List[str]:
    """Rút trích các từ khóa ngành/nghề mà người dùng quan tâm"""
    norm = normalize_vietnamese_text(text)
    common_fields = [
        "công nghệ thông tin", "khoa học máy tính", "lập trình web", "lập trình phần mềm",
        "trí tuệ nhân tạo", "an toàn thông tin", "an ninh mạng", "khoa học dữ liệu",
        "kinh tế", "quản trị kinh doanh", "tài chính ngân hàng", "kế toán", "kiểm toán",
        "marketing", "truyền thông", "thiết kế đồ họa", "logistics", "chuỗi cung ứng",
        "kỹ thuật ô tô", "cơ điện tử", "tự động hóa", "y đa khoa", "dược học", "ngôn ngữ anh"
    ]
    matched = [f for f in common_fields if f in norm]
    return matched


def parse_student_prompt(prompt: str, target_year: int = 2026) -> ExtractedIntent:
    """
    Hàm phân tích cốt lõi: Tiếp nhận prompt tự do của học sinh và bóc tách thành ExtractedIntent.
    """
    score = extract_student_score(prompt)
    group_code = extract_group_code(prompt)
    budget = extract_budget(prompt)
    city = extract_city(prompt)
    height, eye, gender = extract_physical_traits(prompt)
    holland = infer_holland_code(prompt)
    career_kws = extract_career_keywords(prompt)

    # Defaults thông minh nếu không đề cập
    if score is None:
        score = 25.0  # Điểm giả định trung bình khá nếu học sinh chỉ hỏi định hướng
    if group_code is None:
        group_code = "A00"  # Khối phổ biến nhất nếu chưa rõ
    if budget is None:
        budget = 50_000_000  # Mức ngân sách mặc định đủ bao quát đại học công lập

    return ExtractedIntent(
        student_score=score,
        student_group_code=group_code,
        target_year=target_year,
        max_annual_budget=budget,
        preferred_city=city,
        student_gender=gender,
        student_height=height,
        student_eye_degree=eye,
        inferred_holland_code=holland,
        target_career_keywords=career_kws,
        raw_prompt=prompt
    )
