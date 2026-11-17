"""Build recommendation inputs from the authenticated student's stored profile."""
from fastapi import HTTPException
from app.modules.students.service import get_full_student_profile
from .query_parser import (parse_student_prompt, extract_student_score, extract_group_code,
                           extract_budget, extract_physical_traits, extract_city)

GROUPS = {
    'A00': ('Toán', 'Vật lý', 'Hóa học'),
    'A01': ('Toán', 'Vật lý', 'Tiếng Anh'),
    'B00': ('Toán', 'Hóa học', 'Sinh học'),
    'C00': ('Ngữ văn', 'Lịch sử', 'Địa lý'),
    'D01': ('Toán', 'Ngữ văn', 'Tiếng Anh'),
}


def build_profile_intent(profile, prompt, target_year, previous_prompts=None):
    sources=[prompt]+list(previous_prompts or [])
    def first(extract):
        return next((v for text in sources if (v:=extract(text)) is not None),None)
    intent = parse_student_prompt(prompt, target_year=target_year)
    academic, background, health = profile.academic, profile.background, profile.health
    # Scores are THPT /30 only. Never substitute GPA, IELTS, or DGNL scores.
    subjects = academic.get('subject_scores') or {}
    totals = {group: round(sum(subjects[s] for s in names), 2)
              for group, names in GROUPS.items()
              if all(isinstance(subjects.get(s), (int, float)) and 0 <= subjects[s] <= 10 for s in names)}
    explicit_group = first(extract_group_code)
    explicit_score = first(extract_student_score)
    group = explicit_group or (max(totals, key=totals.get) if totals else None)
    score = explicit_score if explicit_score is not None else totals.get(group)
    if group is None or score is None:
        raise HTTPException(422, 'Vui lòng nhập đủ điểm ba môn của một tổ hợp trong hồ sơ, hoặc nêu rõ khối thi và tổng điểm THPT trong câu hỏi. Không dùng GPA thay điểm thi.')
    if not 0 <= score <= 30:
        raise HTTPException(422, 'Luồng tư vấn này dùng điểm THPT thang 30. Vui lòng không nhập điểm ĐGNL/ĐGTD vào tổng điểm THPT.')
    riasec = profile.latest_riasec
    if not riasec or not riasec.get('result_code'):
        raise HTTPException(422, 'Vui lòng hoàn thành và lưu bài trắc nghiệm RIASEC trước khi nhận tư vấn theo hồ sơ.')
    intent.student_group_code = group
    intent.student_score = score
    intent.inferred_holland_code = riasec['result_code'][:3].upper()
    budget = first(extract_budget)
    intent.max_annual_budget = budget if budget is not None else background.get('max_annual_tuition')
    intent.preferred_city = first(extract_city)
    height = first(lambda text:extract_physical_traits(text)[0])
    eye = first(lambda text:extract_physical_traits(text)[1])
    gender = first(lambda text:extract_physical_traits(text)[2] if extract_physical_traits(text)[2]!='Any' else None) or 'Any' 
    intent.student_height = height if height is not None else health.get('height_cm')
    eyes = [health[k] for k in ('eye_degree_left', 'eye_degree_right') if health.get(k) is not None]
    intent.student_eye_degree = eye if eye is not None else (max(eyes) if eyes else None)
    intent.student_gender = gender if gender != 'Any' else profile.gender
    # Only non-identifying educational context is provided to the language model.
    intent.profile_context = {
        'score_source': 'question' if explicit_score is not None else 'stored_subject_scores',
        'group_source': 'question' if explicit_group else 'highest_complete_subject_group',
        'gpa_5_semesters': academic.get('gpa_5_semesters'),
        'ielts_score': academic.get('ielts_score'),
        'dgnl_hcm_score': academic.get('dgnl_hcm_score'),
        'hometown_province': background.get('hometown_province'),
        'priority_zone': background.get('priority_zone'),
        'weight_kg': health.get('weight_kg'),
        'mbti': profile.latest_mbti.get('result_code') if profile.latest_mbti else None,
        'riasec_source': 'stored_assessment',
        'tuition_note': 'Học phí tư vấn dùng mức tối đa cấp trường khi chưa có học phí riêng cho chương trình; không bảo đảm áp dụng cho mọi hệ đào tạo.',
        'note': 'Điểm THPT chưa cộng ưu tiên. Không suy đoán dữ liệu trống; thể lực chưa nhập chưa được xác minh. Quê quán không phải nơi muốn học. GPA/ĐGNL/IELTS không thay thế điểm THPT.',
    }
    return intent


def resolve_profile_intent(db, user, request):
    conversation=getattr(request,'conversation',[])
    previous=[m['content'] for m in conversation[:-1] if m.get('role')=='user'][-6:][::-1]
    return build_profile_intent(get_full_student_profile(db, user.user_id), request.prompt, request.target_year, previous)
