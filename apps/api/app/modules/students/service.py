"""
Student Profile Service.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.models_db import (
    User,
    StudentProfile,
    StudentBackground,
    AcademicProfile,
    HealthProfile,
    PersonalityResult,
)
from .schemas import (
    StudentProfileUpdate,
    BackgroundUpdate,
    AcademicUpdate,
    HealthUpdate,
    FullStudentResponse,
    ImportLocalProfileRequest,
)

# Bảng quy đổi điểm ưu tiên khu vực theo Quy chế Tuyển sinh của Bộ GD&ĐT
PRIORITY_ZONE_POINTS = {
    "KV1": 0.75,
    "KV2-NT": 0.5,
    "KV2": 0.25,
    "KV3": 0.0,
}

# Bảng quy đổi điểm ưu tiên đối tượng chính sách
PRIORITY_OBJECT_POINTS = {
    "01": 2.0,
    "02": 2.0,
    "03": 2.0,
    "04": 2.0,
    "05": 1.0,
    "06": 1.0,
    "07": 1.0,
    "UT1": 2.0,
    "UT2": 1.0,
    "None": 0.0,
}


def calculate_priority_points(zone: str, obj: str, total_score: float = 0.0) -> float:
    """
    Công thức tính điểm ưu tiên động chuẩn Quy chế Tuyển sinh 2025:
    Nếu tổng điểm xét tuyển >= 22.5:
        Điểm ưu tiên = [(30 - Tổng điểm) / 7.5] * (Điểm KV + Điểm ĐT)
    Nếu tổng điểm < 22.5:
        Điểm ưu tiên = Điểm KV + Điểm ĐT
    """
    z_pts = PRIORITY_ZONE_POINTS.get(zone, 0.0)
    o_pts = PRIORITY_OBJECT_POINTS.get(obj, 0.0)
    raw_priority = z_pts + o_pts
    if total_score < 22.5 or total_score <= 0.0:
        return round(raw_priority, 2)
    elif total_score >= 30.0:
        return 0.0
    else:
        return round(((30.0 - total_score) / 7.5) * raw_priority, 2)


def get_full_student_profile(db: Session, student_id: str) -> FullStudentResponse:
    profile = db.query(StudentProfile).filter(StudentProfile.student_id == student_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Hồ sơ học sinh không tồn tại.")
    
    user = db.query(User).filter(User.user_id == student_id).first()
    bg = db.query(StudentBackground).filter(StudentBackground.student_id == student_id).first()
    acad = db.query(AcademicProfile).filter(AcademicProfile.student_id == student_id).first()
    hlth = db.query(HealthProfile).filter(HealthProfile.student_id == student_id).first()

    # Lấy kết quả RIASEC mới nhất (bảo toàn Stage 1 độc lập)
    latest_riasec = (
        db.query(PersonalityResult)
        .filter(PersonalityResult.student_id == student_id, PersonalityResult.test_type == "RIASEC")
        .order_by(PersonalityResult.completed_at.desc())
        .first()
    )

    # Lấy kết quả MBTI mới nhất
    latest_mbti = (
        db.query(PersonalityResult)
        .filter(PersonalityResult.student_id == student_id, PersonalityResult.test_type == "MBTI")
        .order_by(PersonalityResult.completed_at.desc())
        .first()
    )

    return FullStudentResponse(
        student_id=profile.student_id,
        email=user.email if user else "",
        first_name=profile.first_name,
        last_name=profile.last_name,
        dob=profile.dob,
        gender=profile.gender,
        phone=profile.phone,
        current_school=profile.current_school,
        grade_level=profile.grade_level,
        target_year=profile.target_year,
        background={
            "hometown_province": bg.hometown_province if bg else None,
            "income_level": bg.income_level if bg else "Medium",
            "max_annual_tuition": bg.max_annual_tuition if bg else 30000000,
            "priority_zone": bg.priority_zone if bg else "KV3",
            "priority_object": bg.priority_object if bg else "None",
            "priority_points_calculated": bg.priority_points_calculated if bg else 0.0,
            "financial_hardship": bg.financial_hardship if bg else False,
        },
        academic={
            "gpa_grade_10": acad.gpa_grade_10 if acad else None,
            "gpa_grade_11": acad.gpa_grade_11 if acad else None,
            "gpa_grade_12": acad.gpa_grade_12 if acad else None,
            "gpa_5_semesters": acad.gpa_5_semesters if acad else None,
            "academic_rank": acad.academic_rank if acad else None,
            "conduct_grade_10": acad.conduct_grade_10 if acad else None,
            "conduct_grade_11": acad.conduct_grade_11 if acad else None,
            "conduct_grade_12": acad.conduct_grade_12 if acad else None,
            "ielts_score": acad.ielts_score if acad else None,
            "sat_score": acad.sat_score if acad else None,
            "dgnl_hcm_score": acad.dgnl_hcm_score if acad else None,
            "dgnl_hn_score": acad.dgnl_hn_score if acad else None,
            "tsa_hust_score": acad.tsa_hust_score if acad else None,
            "subject_scores": acad.subject_scores if acad else {},
            "exam_scores": acad.exam_scores if acad else {},
        },
        health={
            "height_cm": hlth.height_cm if hlth else None,
            "weight_kg": hlth.weight_kg if hlth else None,
            "bmi": hlth.bmi if hlth else None,
            "eye_degree_left": hlth.eye_degree_left if hlth else None,
            "eye_degree_right": hlth.eye_degree_right if hlth else None,
            "max_eye_degree": hlth.max_eye_degree if hlth else None,
            "color_blindness": hlth.color_blindness if hlth else False,
            "hearing_status": hlth.hearing_status if hlth else "Normal",
            "has_health_certificate": hlth.has_health_certificate if hlth else False,
        },
        latest_riasec={
            "result_code": latest_riasec.result_code,
            "scores_detail": latest_riasec.scores_detail,
            "top_traits": latest_riasec.top_traits,
            "title": latest_riasec.title,
            "summary": latest_riasec.summary,
            "completed_at": latest_riasec.completed_at.isoformat(),
        } if latest_riasec else None,
        latest_mbti={
            "result_code": latest_mbti.result_code,
            "scores_detail": latest_mbti.scores_detail,
            "top_traits": latest_mbti.top_traits,
            "title": latest_mbti.title,
            "summary": latest_mbti.summary,
            "completed_at": latest_mbti.completed_at.isoformat(),
        } if latest_mbti else None,
    )


def update_student_profile(db: Session, student_id: str, req: StudentProfileUpdate):
    profile = db.query(StudentProfile).filter(StudentProfile.student_id == student_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Hồ sơ không tồn tại.")
    
    for field, val in req.dict(exclude_unset=True).items():
        setattr(profile, field, val)
    profile.updated_at = datetime.utcnow()
    db.commit()
    return get_full_student_profile(db, student_id)


def update_student_background(db: Session, student_id: str, req: BackgroundUpdate):
    bg = db.query(StudentBackground).filter(StudentBackground.student_id == student_id).first()
    if not bg:
        bg = StudentBackground(student_id=student_id)
        db.add(bg)

    for field, val in req.dict(exclude_unset=True).items():
        setattr(bg, field, val)

    # Tự động nhận diện khu vực ưu tiên từ Tỉnh / Thành quê quán
    if bg.hometown_province:
        from app.modules.consultation.parser import PROVINCE_PRIORITY_MAP
        prov_clean = bg.hometown_province.strip().lower()
        for prov_key, (z_code, _) in PROVINCE_PRIORITY_MAP.items():
            if prov_key in prov_clean:
                bg.priority_zone = z_code
                break

    # Tính điểm ưu tiên động chuẩn 2025 theo điểm xét tuyển thực tế
    acad = db.query(AcademicProfile).filter(AcademicProfile.student_id == student_id).first()
    total_score = 0.0
    if acad and acad.exam_scores and isinstance(acad.exam_scores, dict):
        scores = [float(v) for v in acad.exam_scores.values() if isinstance(v, (int, float))]
        if scores:
            total_score = max(scores)

    bg.priority_points_calculated = calculate_priority_points(bg.priority_zone, bg.priority_object, total_score)
    db.commit()
    return get_full_student_profile(db, student_id)


def update_academic_profile(db: Session, student_id: str, req: AcademicUpdate):
    acad = db.query(AcademicProfile).filter(AcademicProfile.student_id == student_id).first()
    if not acad:
        acad = AcademicProfile(student_id=student_id)
        db.add(acad)

    for field, val in req.dict(exclude_unset=True).items():
        setattr(acad, field, val)
    acad.updated_at = datetime.utcnow()
    db.commit()
    return get_full_student_profile(db, student_id)


def update_health_profile(db: Session, student_id: str, req: HealthUpdate):
    hlth = db.query(HealthProfile).filter(HealthProfile.student_id == student_id).first()
    if not hlth:
        hlth = HealthProfile(student_id=student_id)
        db.add(hlth)

    for field, val in req.dict(exclude_unset=True).items():
        setattr(hlth, field, val)

    # Tính BMI tự động nếu có chiều cao và cân nặng
    if hlth.height_cm and hlth.weight_kg and hlth.height_cm > 0:
        h_m = hlth.height_cm / 100.0
        hlth.bmi = round(hlth.weight_kg / (h_m * h_m), 1)

    # Tính max_eye_degree
    eyes = [e for e in [hlth.eye_degree_left, hlth.eye_degree_right] if e is not None]
    if eyes:
        hlth.max_eye_degree = max(eyes)

    db.commit()
    return get_full_student_profile(db, student_id)


def import_local_profile(db: Session, student_id: str, req: ImportLocalProfileRequest):
    """Import và đồng bộ dữ liệu khách từ localStorage vào tài khoản đã đăng nhập."""
    if req.background:
        update_student_background(db, student_id, BackgroundUpdate(**req.background))
    if req.academic:
        update_academic_profile(db, student_id, AcademicUpdate(**req.academic))
    if req.health:
        update_health_profile(db, student_id, HealthUpdate(**req.health))

    # Import các bài test từ localStorage (tránh duplicate)
    if req.quiz_results:
        for item in req.quiz_results:
            t_type = item.get("test_type", "").upper()
            code = item.get("result_code", "")
            if not t_type or not code:
                continue
            
            # Check exist
            existing = (
                db.query(PersonalityResult)
                .filter(
                    PersonalityResult.student_id == student_id,
                    PersonalityResult.test_type == t_type,
                    PersonalityResult.result_code == code,
                )
                .first()
            )
            if not existing:
                res = PersonalityResult(
                    student_id=student_id,
                    test_type=t_type,
                    result_code=code,
                    scores_detail=item.get("scores_detail", {}),
                    top_traits=item.get("top_traits", []),
                    title=item.get("title", ""),
                    summary=item.get("summary", ""),
                    completed_at=datetime.utcnow(),
                )
                db.add(res)
        db.commit()

    return get_full_student_profile(db, student_id)
