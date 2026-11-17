"""
Agent Tools and Deterministic Retrieval for GraphRAG Consultation.
Provides strict schema, input validation, and exact provenance evidence.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.models_db import (
    University,
    Program,
    AdmissionCriteria,
    StudentProfile,
    StudentBackground,
    AcademicProfile,
    HealthProfile,
)


def get_profile_tool(db: Session, student_id: str) -> Dict[str, Any]:
    """Tool 1: get_profile - Truy xuất hồ sơ điểm số, học tập, thể lực của học sinh"""
    p = db.query(StudentProfile).filter(StudentProfile.student_id == student_id).first()
    if not p:
        return {"error": "Hồ sơ không tồn tại"}
    
    bg = db.query(StudentBackground).filter(StudentBackground.student_id == student_id).first()
    acad = db.query(AcademicProfile).filter(AcademicProfile.student_id == student_id).first()
    hlth = db.query(HealthProfile).filter(HealthProfile.student_id == student_id).first()

    return {
        "student_id": p.student_id,
        "name": f"{p.last_name} {p.first_name}",
        "grade_level": p.grade_level,
        "target_year": p.target_year,
        "priority_points": bg.priority_points_calculated if bg else 0.0,
        "max_tuition": bg.max_annual_tuition if bg else 0,
        "gpa_overall": acad.gpa_overall if acad else None,
        "exam_scores": acad.exam_scores if acad else {},
        "height_cm": hlth.height_cm if hlth else None,
        "max_eye_degree": hlth.max_eye_degree if hlth else None,
    }


def search_programs_tool(
    db: Session, keyword: str, city: Optional[str] = None, group_code: Optional[str] = None, limit: int = 10
) -> List[Dict[str, Any]]:
    """Tool 2: search_programs - Tìm kiếm chương trình đào tạo theo từ khóa ngành và thành phố"""
    q = db.query(Program, University).join(University, Program.uni_id == University.uni_id)
    if keyword:
        q = q.filter(Program.name.ilike(f"%{keyword.strip()}%"))
    if city:
        q = q.filter(University.location.ilike(f"%{city.strip()}%"))

    items = q.limit(limit).all()
    out = []
    for prog, uni in items:
        crit = db.query(AdmissionCriteria).filter(AdmissionCriteria.program_id == prog.program_id).first()
        out.append({
            "program_id": prog.program_id,
            "program_name": prog.name,
            "major_code": prog.major_code,
            "university_name": uni.name,
            "location": uni.location,
            "tuition_annual": prog.effective_cost,
            "benchmark_score": crit.benchmark_score if crit else None,
            "minimum_threshold": crit.minimum_threshold if crit else None,
        })
    return out


def check_eligibility_tool(
    db: Session, program_id: str, student_score: float, bonus_points: float = 0.0
) -> Dict[str, Any]:
    """Tool 3: check_eligibility - Đối chiếu điều kiện trúng tuyển và điểm sàn"""
    prog = db.query(Program).filter(Program.program_id == program_id).first()
    if not prog:
        return {"error": "Không tìm thấy chương trình đào tạo"}

    criteria = db.query(AdmissionCriteria).filter(AdmissionCriteria.program_id == program_id).all()
    if not criteria:
        return {"status": "Chưa đủ thông tin", "reason": "Chưa có dữ liệu tiêu chí tuyển sinh cho ngành này"}

    total_score = student_score + bonus_points
    eligible_methods = []
    for c in criteria:
        if c.benchmark_score is not None:
            margin = total_score - c.benchmark_score
            is_pass = margin >= 0
            eligible_methods.append({
                "method": c.method,
                "benchmark_score": c.benchmark_score,
                "minimum_threshold": c.minimum_threshold,
                "score_margin": round(margin, 2),
                "is_eligible": is_pass,
                "safety_level": "Safe" if margin >= 1.5 else ("Target" if margin >= 0 else "Reach")
            })

    return {
        "program_id": prog.program_id,
        "program_name": prog.name,
        "student_total_score": total_score,
        "evaluation_methods": eligible_methods,
        "note": "Điểm chuẩn lịch sử chỉ mang tính tham khảo, không bảo đảm trúng tuyển."
    }


def compare_programs_tool(db: Session, program_ids: List[str]) -> List[Dict[str, Any]]:
    """Tool 4: compare_programs - So sánh trực tiếp từ 2 đến 4 chương trình đào tạo"""
    out = []
    for pid in program_ids[:4]:
        prog = db.query(Program).filter(Program.program_id == pid).first()
        if not prog:
            continue
        uni = db.query(University).filter(University.uni_id == prog.uni_id).first()
        crit = db.query(AdmissionCriteria).filter(AdmissionCriteria.program_id == pid).all()
        
        benchmarks = [f"{c.method}: {c.benchmark_score}" for c in crit if c.benchmark_score]
        out.append({
            "program_id": prog.program_id,
            "program_name": prog.name,
            "major_code": prog.major_code,
            "university_name": uni.name if uni else "",
            "location": uni.location if uni else "",
            "tuition_annual": prog.effective_cost,
            "is_subsidized": prog.is_subsidized,
            "duration_years": prog.duration_years,
            "benchmarks": benchmarks,
            "has_dormitory": uni.has_dormitory if uni else False,
        })
    return out


def get_source_evidence_tool(db: Session, program_id: str) -> Dict[str, Any]:
    """Tool 5: get_source_evidence - Lấy thông tin nguồn dẫn chứng (provenance) chính thức"""
    prog = db.query(Program).filter(Program.program_id == program_id).first()
    if not prog:
        return {"error": "Không tìm thấy chương trình đào tạo"}

    uni = db.query(University).filter(University.uni_id == prog.uni_id).first()
    criteria = db.query(AdmissionCriteria).filter(AdmissionCriteria.program_id == program_id).all()

    evidence_sources = []
    for c in criteria:
        evidence_sources.append({
            "criteria_id": c.criteria_id,
            "year": c.year,
            "method": c.method,
            "group_code": c.group_code,
            "benchmark_score": c.benchmark_score,
            "minimum_threshold": c.minimum_threshold,
            "source_url": c.source_url or (uni.admissions_url if uni else None),
        })

    return {
        "program_id": prog.program_id,
        "program_name": prog.name,
        "university_name": uni.name if uni else "",
        "admissions_portal": uni.admissions_url if uni else "",
        "evidence_records": evidence_sources,
        "verification_notice": "Dữ liệu được trích xuất từ đề án tuyển sinh 2026 chính thức."
    }

