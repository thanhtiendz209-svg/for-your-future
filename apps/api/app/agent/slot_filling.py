"""
Slot Filling and Safe State Merging Module for Conversational Career Guidance Agent.
Ensures that missing/None fields never overwrite previously collected valid student slots.
"""

import copy
import json
import logging
import re
from typing import Dict, Any, List, Optional

try:
    from app.modules.graphrag.llm_service import call_gemini_chat
    from .prompts import LLM_SLOT_EXTRACTION_PROMPT
except ImportError:
    try:
        from ..modules.graphrag.llm_service import call_gemini_chat
        from .prompts import LLM_SLOT_EXTRACTION_PROMPT
    except ImportError:
        from llm_service import call_gemini_chat
        from agent.prompts import LLM_SLOT_EXTRACTION_PROMPT

logger = logging.getLogger("graphrag.agent.slots")

DEFAULT_SLOTS: Dict[str, Any] = {
    "student_score": None,
    "student_group_code": None,
    "target_major_keywords": [],
    "target_university": None,
    "target_university_code": None,
    "is_military_interest": False,
    "preferred_city": None,
    "max_annual_budget": None,
    "inferred_holland_code": None,
    "bonus_points": 0.0,
    "student_eye_degree": None,
    "student_height": None
}


def merge_slots(
    existing_slots: Optional[Dict[str, Any]],
    new_slots: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Hàm gộp Slot an toàn (Safe Slot Merging):
    QUY TẮC CỐT LÕI:
    1. Các giá trị None hoặc rỗng trong new_slots TUYỆT ĐỐI KHÔNG ĐƯỢC ghi đè lên dữ liệu đã có.
       Ví dụ: Lượt 1 đã có group='A00', Lượt 2 user chỉ nhập score=25 -> Kết quả phải là {group: 'A00', score: 25}.
    2. Nếu new_slots cung cấp giá trị mới hợp lệ (số > 0, chuỗi không rỗng), giá trị mới sẽ cập nhật.
    3. Dạng danh sách (như target_major_keywords) được kết hợp và loại bỏ phần tử trùng lặp.
    """
    result = copy.deepcopy(DEFAULT_SLOTS)
    if existing_slots:
        for k, v in existing_slots.items():
            if v is not None:
                result[k] = copy.deepcopy(v)

    if not new_slots:
        return result

    for key, new_val in new_slots.items():
        if new_val is None:
            continue

        # Xử lý chuỗi
        if isinstance(new_val, str):
            clean_str = new_val.strip()
            if clean_str:
                result[key] = clean_str
            continue

        # Xử lý danh sách (Keywords): Hợp nhất không trùng lặp
        if isinstance(new_val, list):
            if new_val:
                clean_kws = [str(item).strip() for item in new_val if str(item).strip()]
                if clean_kws:
                    old_list = result.get(key, [])
                    if isinstance(old_list, list) and old_list:
                        result[key] = list(dict.fromkeys(old_list + clean_kws))
                    else:
                        result[key] = clean_kws
            continue

        # Xử lý boolean (is_military_interest)
        if isinstance(new_val, bool):
            if new_val:
                result[key] = True
            continue

        # Xử lý số (Score, Budget, Degree, Height)
        if isinstance(new_val, (int, float)):
            # Score hợp lệ phải > 0
            if key == "student_score":
                if new_val > 0.0:
                    result[key] = float(new_val)
            elif key == "max_annual_budget":
                if new_val > 0:
                    result[key] = int(new_val)
            elif key == "bonus_points":
                result[key] = float(new_val)
            else:
                result[key] = new_val
            continue

        # Các kiểu dữ liệu khác
        result[key] = new_val

    return result


def extract_slots_from_prompt(prompt: str) -> Dict[str, Any]:
    """
    Bóc tách các slot thô bằng Regex dự phòng trong trường hợp Gemini LLM gặp sự cố mạng.
    Chỉ trả về các trường phát hiện được trong câu hỏi.
    """
    slots = copy.deepcopy(DEFAULT_SLOTS)

    # 1. Điểm thi (vd: "25 điểm", "25.5 đ", "được 26 điểm", "dự kiến là 24")
    # Tránh bắt nhầm số cuối của khối thi như "A01 điểm"
    score_match = re.search(r'(?<![A-Za-z0-9])(\d{1,2}(?:\.\d{1,2})?)\s*(?:đ|điểm|\.đ)', prompt, re.IGNORECASE)
    if not score_match:
        score_match = re.search(r'(?:đạt|được|thi|tầm|khoảng|là)\s*(\d{1,2}(?:\.\d{1,2})?)', prompt, re.IGNORECASE)
    if score_match:
        try:
            val = float(score_match.group(1))
            if 0.0 <= val <= 30.0:
                slots["student_score"] = val
        except (ValueError, TypeError):
            pass

    # 2. Khối thi (A00, A01, B00, C00, D01, D07,...)
    group_match = re.search(r'\b([A-D]\d{2})\b', prompt, re.IGNORECASE)
    if group_match:
        slots["student_group_code"] = group_match.group(1).upper()

    # 3. Mức học phí (vd: "20tr", "20 triệu", "25tr/năm")
    budget_match = re.search(r'(\d+)\s*(?:tr|triệu|k)', prompt, re.IGNORECASE)
    if budget_match:
        try:
            val = int(budget_match.group(1))
            if val < 500:
                slots["max_annual_budget"] = val * 1_000_000
        except (ValueError, TypeError):
            pass

    # 4. Tỉnh thành
    p_lower = prompt.lower()
    if any(k in p_lower for k in ["hcm", "hồ chí minh", "tp.hcm", "sài gòn"]):
        slots["preferred_city"] = "TP.HCM"
    elif any(k in p_lower for k in ["hà nội", "hn"]):
        slots["preferred_city"] = "Hà Nội"
    elif any(k in p_lower for k in ["đà nẵng", "đn"]):
        slots["preferred_city"] = "Đà Nẵng"

    # 5. Trường Đại học quan tâm (Tên viết tắt / Mã trường)
    uni_patterns = [
        (r'\b(iuh)\b', "IUH", "Trường Đại học Công nghiệp TP.HCM (IUH)"),
        (r'\b(hcmut|bku)\b', "HCMUT", "Trường Đại học Bách khoa - ĐHQG TP.HCM (HCMUT)"),
        (r'\b(hust)\b', "HUST", "Đại học Bách khoa Hà Nội (HUST)"),
        (r'\b(uit)\b', "UIT", "Trường Đại học Công nghệ Thông tin - ĐHQG TP.HCM (UIT)"),
        (r'\b(ueh)\b', "UEH", "Đại học Kinh tế TP.HCM (UEH)"),
        (r'\b(hutech)\b', "HUTECH", "Trường Đại học Công nghệ TP.HCM (HUTECH)"),
        (r'\b(mta)\b', "MTA", "Học viện Kỹ thuật Quân sự (MTA)"),
        (r'\b(ptit)\b', "PTIT", "Học viện Công nghệ Bưu chính Viễn thông (PTIT)"),
        (r'\b(hcmue)\b', "HCMUE", "Trường Đại học Sư phạm TP.HCM (HCMUE)"),
        (r'(?:đại học|trường|đh)\s+sư phạm tp\.?hcm', "HCMUE", "Trường Đại học Sư phạm TP.HCM (HCMUE)"),
        (r'\b(ou)\b', "OU", "Trường Đại học Mở TP.HCM (OU)"),
        (r'(?:đại học|trường|đh)\s+mở tp\.?hcm', "OU", "Trường Đại học Mở TP.HCM (OU)"),
        (r'\b(tnue)\b', "TNUE", "Trường Đại học Sư phạm - ĐH Thái Nguyên (TNUE)"),
        (r'\b(hnue)\b', "HNUE", "Trường Đại học Sư phạm Hà Nội (HNUE)"),
        (r'(?:đại học|trường|đh)\s+(?:công nghiệp tp\.?hcm|công nghiệp sài gòn)', "IUH", "Trường Đại học Công nghiệp TP.HCM (IUH)"),
        (r'(?:đại học|trường|đh)\s+bách khoa tp\.?hcm', "HCMUT", "Trường Đại học Bách khoa - ĐHQG TP.HCM (HCMUT)"),
        (r'(?:đại học|trường|đh)\s+bách khoa hà nội', "HUST", "Đại học Bách khoa Hà Nội (HUST)"),
        (r'(?:đại học|trường|đh)\s+kinh tế quốc dân', "NEU", "Trường Đại học Kinh tế Quốc dân (NEU)"),
    ]
    for pat, code, name in uni_patterns:
        if re.search(pat, p_lower):
            slots["target_university_code"] = code
            slots["target_university"] = name
            break

    # Trích xuất trường đại học động nếu chưa bắt được bằng pattern
    if not slots.get("target_university"):
        dyn_uni = re.search(r'(?:trường\s+)?(đại học\s+[A-Za-zÀ-ỹ\s\-\/\(\)]+?)(?:\s+ở|\s+tại|\s+có|\.|\,|$)', prompt, re.IGNORECASE)
        if dyn_uni:
            slots["target_university"] = dyn_uni.group(1).strip()

    # 6. Nguyện vọng quân đội / sĩ quan / công an
    military_kws = ["quân sự", "quân đội", "sĩ quan", "học viện kỹ thuật quân sự", "hậu cần", "công binh", "an ninh", "công an"]
    if any(k in p_lower for k in military_kws):
        slots["is_military_interest"] = True

    # 7. Mã Holland hoặc tính cách
    holland_match = re.search(r'\b([R][I][A-Z]{0,2}|[I][R][A-Z]{0,2}|[S][E][A-Z]{0,2})\b', prompt, re.IGNORECASE)
    if holland_match:
        slots["inferred_holland_code"] = holland_match.group(1).upper()
    elif "intj" in p_lower:
        slots["inferred_holland_code"] = "IRC"
        if not slots.get("target_major_keywords"):
            slots["target_major_keywords"] = ["Công nghệ thông tin", "Khoa học máy tính", "Kỹ thuật", "Trí tuệ nhân tạo"]

    # 8. Từ khóa ngành/nghề động từ câu prompt (ví dụ: "nghề Công nghệ thông tin", "ngành Hoá học")
    dyn_career = re.search(r'(?:nghề|ngành)\s+([A-Za-zÀ-ỹ\s\/\-]+?)(?:\.|\,|\s+tại|\s+ở|\s+của|\s+nhờ|\s+cho|\s+đào\s+tạo|$)', prompt, re.IGNORECASE)
    if dyn_career:
        c_name = dyn_career.group(1).strip()
        stop_phrases = {
            "này", "gì", "nào", "đào tạo", "đào tạo nổi bật", "đào tạo tốt", "nổi bật", "hot", 
            "mũi nhọn", "học tập", "tuyển sinh", "các ngành", "nhóm ngành", "ngành gì", "nghề gì",
            "đại học", "trường này", "trường đó", "thông tin"
        }
        if len(c_name) >= 3 and c_name.lower() not in stop_phrases:
            slots["target_major_keywords"] = [c_name]

    # 9. Từ khóa ngành học cơ bản (Dự phòng khi Gemini LLM bị timeout hoặc 429)
    major_candidates = [
        "công nghệ thông tin", "khoa học máy tính", "kỹ thuật phần mềm", "trí tuệ nhân tạo", "an toàn thông tin",
        "khoa học dữ liệu", "điện - điện tử", "điện tử viễn thông", "cơ điện tử", "tự động hóa", "kỹ thuật cơ khí",
        "kỹ thuật ô tô", "logistics", "quản trị chuỗi cung ứng", "kế toán", "kiểm toán", "tài chính ngân hàng",
        "quản trị kinh doanh", "marketing", "y đa khoa", "dược học", "điều dưỡng", "thiết kế đồ họa", "ngôn ngữ anh",
        "hoá học", "hóa học", "sư phạm", "vật lý", "toán học", "sinh học"
    ]
    detected_kws = [mk for mk in major_candidates if mk in p_lower]
    if detected_kws:
        if not slots.get("target_major_keywords"):
            slots["target_major_keywords"] = detected_kws
        else:
            slots["target_major_keywords"] = list(dict.fromkeys(slots["target_major_keywords"] + detected_kws))
    return slots


async def extract_slots_with_llm(
    prompt: str,
    messages: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Trích xuất thực thể, điểm số, khối thi, học phí và ý định bằng LLM Google Gemini (Zero-Hardcode NLU).
    Có khả năng thấu hiểu mọi cách diễn đạt tiếng Việt tự nhiên và fallback regex tự động khi cần.
    """
    llm_prompt = LLM_SLOT_EXTRACTION_PROMPT.format(user_prompt=prompt)
    conv_messages = []
    if messages:
        for m in messages[-4:]:
            # Chỉ nạp tin nhắn của User để không bị ảnh hưởng bởi các con số cũ do AI phát biểu
            if m.get("role") == "user" and m.get("content"):
                conv_messages.append({"role": "user", "content": m.get("content")})
    conv_messages.append({"role": "user", "content": llm_prompt})

    raw_resp = await call_gemini_chat(conv_messages, temperature=0.1, max_tokens=300)

    slots: Optional[Dict[str, Any]] = None
    if raw_resp:
        try:
            cleaned = raw_resp.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)
            data = json.loads(cleaned)
            if isinstance(data, dict):
                score = data.get("student_score")
                if score is not None:
                    try:
                        score = float(score)
                        if score <= 0.0 or score > 30.0:
                            score = None
                    except (ValueError, TypeError):
                        score = None

                group = data.get("student_group_code")
                if group:
                    group = str(group).upper().strip()

                city = data.get("preferred_city")
                if city:
                    city_str = str(city).strip()
                    if city_str.lower() in ("hcm", "tp hcm", "tp.hcm", "tphcm", "hồ chí minh", "sài gòn", "sg"):
                        city = "TP.HCM"
                    else:
                        city = city_str

                budget = data.get("max_annual_budget")
                if budget is not None:
                    try:
                        budget = int(budget)
                        if budget <= 0:
                            budget = None
                    except (ValueError, TypeError):
                        budget = None

                kws = data.get("target_major_keywords") or []
                if not isinstance(kws, list):
                    kws = [str(kws)]

                holland = data.get("inferred_holland_code")
                if holland and str(holland).lower() not in ("null", "none", ""):
                    holland = str(holland).upper().strip()[:3]
                    if len(holland) < 3:
                        for ch in "RIASEC":
                            if ch not in holland:
                                holland += ch
                            if len(holland) >= 3:
                                break
                else:
                    holland = None

                target_uni = data.get("target_university")
                target_code = data.get("target_university_code")
                if target_code:
                    target_code = str(target_code).upper().strip()
                is_mil = bool(data.get("is_military_interest", False))

                # Regex fallback for university code / military if LLM missed it
                fallback_slots = extract_slots_from_prompt(prompt)
                if not target_code and fallback_slots.get("target_university_code"):
                    target_code = fallback_slots["target_university_code"]
                if not target_uni and fallback_slots.get("target_university"):
                    target_uni = fallback_slots["target_university"]
                if not is_mil and fallback_slots.get("is_military_interest"):
                    is_mil = True

                slots = {
                    "student_score": score,
                    "student_group_code": group,
                    "preferred_city": city,
                    "max_annual_budget": budget,
                    "target_major_keywords": kws,
                    "target_university": target_uni,
                    "target_university_code": target_code,
                    "is_military_interest": is_mil,
                    "inferred_holland_code": holland,
                    "student_height": None,
                    "student_eye_degree": None,
                    "bonus_points": 0.0,
                    "_intent": data.get("intent")
                }
                logger.info(f"[LLM Slot Extractor] Successfully parsed from prompt '{prompt}': score={score}, group={group}, city={city}, uni={target_code}, military={is_mil}")
        except Exception as e:
            logger.warning(f"[LLM Slot Extractor] Parse warning: {e}, falling back to regex")

    if not slots:
        slots = extract_slots_from_prompt(prompt)

    return slots


def enrich_slots_from_db_profile(
    slots: Dict[str, Any],
    profile_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Nạp bổ sung các slot còn thiếu từ Hồ sơ học sinh trong Database (PostgreSQL)
    nếu học sinh chưa đề cập trong hội thoại.
    """
    if not profile_data:
        return slots

    enriched = copy.deepcopy(slots)

    # 1. Bổ sung điểm thi và khối thi từ Academic Profile hoặc flat profile
    academic = profile_data.get("academic") or {}
    exam_scores = academic.get("exam_scores") or {}

    if enriched.get("student_score") is None:
        target_score = exam_scores.get("target_score") or exam_scores.get("score") or profile_data.get("score") or profile_data.get("student_score") or profile_data.get("score_a01") or profile_data.get("score_a00")
        if target_score:
            try:
                enriched["student_score"] = float(target_score)
                logger.info(f"Loaded student_score={enriched['student_score']} from DB profile")
            except (ValueError, TypeError):
                pass

    if enriched.get("student_group_code") is None:
        sub_group = exam_scores.get("subject_group") or profile_data.get("subject_group") or profile_data.get("group_code") or profile_data.get("student_group_code")
        if not sub_group and profile_data.get("score_a01"):
            sub_group = "A01"
        elif not sub_group and profile_data.get("score_a00"):
            sub_group = "A00"
        if sub_group:
            enriched["student_group_code"] = str(sub_group).upper().strip()
            logger.info(f"Loaded student_group_code={enriched['student_group_code']} from DB profile")

    # 2. Bổ sung tỉnh thành và học phí từ Background hoặc flat profile
    background = profile_data.get("background") or {}
    if enriched.get("preferred_city") is None:
        city = background.get("hometown_province") or profile_data.get("preferred_city") or profile_data.get("location") or profile_data.get("city")
        if city:
            enriched["preferred_city"] = city

    if enriched.get("max_annual_budget") is None:
        tuition_mil = background.get("max_annual_tuition") or profile_data.get("max_annual_budget") or profile_data.get("max_tuition") or profile_data.get("budget")
        if tuition_mil:
            try:
                val = float(tuition_mil)
                if val <= 500:  # Đơn vị triệu VND
                    val *= 1_000_000
                enriched["max_annual_budget"] = int(val)
            except (ValueError, TypeError):
                pass

    # 3. Bổ sung tính cách Holland
    personality = profile_data.get("personality") or {}
    if enriched.get("inferred_holland_code") is None:
        holland = personality.get("holland_code") or personality.get("result_code") or profile_data.get("holland_code")
        if holland:
            enriched["inferred_holland_code"] = str(holland).strip()

    # 4. Thể chất
    health = profile_data.get("health") or {}
    if enriched.get("student_height") is None and (health.get("height_cm") or profile_data.get("student_height")):
        enriched["student_height"] = health.get("height_cm") or profile_data.get("student_height")
    if enriched.get("student_eye_degree") is None and health.get("max_eye_degree"):
        enriched["student_eye_degree"] = health.get("max_eye_degree")

    return enriched


def check_missing_slots(slots: Dict[str, Any]) -> List[str]:
    """
    Kiểm tra xem còn thiếu slot cốt lõi nào để thực hiện Cypher Pruning an toàn.
    Hai slot bắt buộc tiên quyết:
    1. 'student_score' (Điểm thi)
    2. 'student_group_code' (Khối thi)
    """
    missing: List[str] = []

    score = slots.get("student_score")
    if score is None or float(score) <= 0.0:
        missing.append("student_score")

    group = slots.get("student_group_code")
    if not group or not str(group).strip():
        missing.append("student_group_code")

    return missing
