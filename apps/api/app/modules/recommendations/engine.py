"""
Deterministic Pruning Engine for Recommendation and Guidance.
Executes mathematical hard-constraint pruning across points, budget, physical health, and Holland alignment.
Queries Neo4j when available with transparent fallback to relational SQL.
"""

import logging
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from app.core.models_db import University, Program, AdmissionCriteria, Career
from app.integrations.neo4j.client import execute_query_sync, check_health as check_neo4j_health
from app.integrations.neo4j.query_builder import CypherQueryBuilder
from .schemas import RecommendationRequest, RecommendationResultItem, RecommendationResponse

logger = logging.getLogger("foryourfuture.engine")

CITY_ALIASES = {
    "sài gòn": "TP.HCM",
    "sai gon": "TP.HCM",
    "tp hcm": "TP.HCM",
    "tphcm": "TP.HCM",
    "tp.hcm": "TP.HCM",
    "hn": "Hà Nội",
    "ha noi": "Hà Nội",
    "đà nẵng": "Đà Nẵng",
    "da nang": "Đà Nẵng",
}


def normalize_city(city: Optional[str]) -> Optional[str]:
    if not city:
        return None
    normalized = city.strip().lower()
    return CITY_ALIASES.get(normalized, city.strip())


def run_deterministic_pruning(
    db: Session, req: RecommendationRequest, limit: int = 15
) -> RecommendationResponse:
    """
    Thực hiện lọc tất định đa tiêu chí.
    Thử nghiệm trên Neo4j trước; nếu Neo4j offline, chạy trên cơ sở dữ liệu quan hệ (PostgreSQL / SQLite).
    """
    preferred_city = normalize_city(req.preferred_city)
    holland_code = req.holland_code.strip().upper()
    primary_holland = holland_code[0] if holland_code else ""
    effective_score = req.student_score + (req.bonus_points or 0.0)

    # 1. Thử truy vấn qua Neo4j Knowledge Graph nếu khả dụng
    try:
        query = CypherQueryBuilder.build_recommendation_query(req, limit=limit)
        params = CypherQueryBuilder.extract_query_parameters(req, limit=limit)
        if preferred_city:
            params["preferred_city"] = preferred_city

        graph_records = execute_query_sync(query, params)
        if graph_records:
            results = []
            for r in graph_records:
                results.append(
                    RecommendationResultItem(
                        university_id=r.get("university_id", ""),
                        university_name=r.get("university_name", ""),
                        university_short_name=r.get("university_short_name"),
                        faculty_ratio=r.get("faculty_ratio"),
                        facilities=r.get("facilities", []),
                        program_id=r.get("program_id", ""),
                        program_name=r.get("program_name", ""),
                        credential=r.get("credential", "Cử nhân"),
                        benchmark_score=float(r.get("benchmark_score", 0.0)),
                        minimum_threshold=r.get("minimum_threshold"),
                        group_code=r.get("group_code") or req.student_group_code,
                        tie_breaker_subject=r.get("tie_breaker_subject", "Toán"),
                        source_url=r.get("source_url") or "https://tuyensinh.edu.vn",
                        score_margin=round(float(r.get("score_margin", 0.0)), 2),
                        official_tuition=int(r.get("official_tuition", 0)),
                        is_subsidized=bool(r.get("is_subsidized", False)),
                        actual_tuition=int(r.get("actual_tuition", 0)),
                        career_name=r.get("career_name", ""),
                        job_growth_rate=float(r.get("job_growth_rate", 0.0)),
                        hiring_companies=r.get("hiring_companies", []),
                        holland_match_score=float(r.get("holland_match_score", 1.0)),
                        city=r.get("city", ""),
                        transport_score=r.get("transport_score"),
                        safety_level=r.get("safety_level", "Safe"),
                    )
                )
            return RecommendationResponse(
                total_found=len(results),
                target_year=req.target_year,
                holland_code=holland_code,
                student_group_code=req.student_group_code,
                results=results,
            )
    except Exception as e:
        logger.info(f"Neo4j query unavailable or not initialized ({e}). Executing relational pruning engine.")

    # 2. Relational Pruning Engine (100% Deterministic trên PostgreSQL / SQLite)
    # Lấy các trường đại học thỏa mãn địa điểm (nếu có)
    uni_query = db.query(University)
    if preferred_city:
        uni_query = uni_query.filter(University.location.ilike(f"%{preferred_city}%"))
    unis = {u.uni_id: u for u in uni_query.all()}
    if not unis:
        return _build_empty_response(req, "Không có trường đại học nào tại thành phố được chọn.")

    # Lấy các tiêu chí tuyển sinh thỏa mãn năm, phương thức, tổ hợp và điểm số
    crit_query = (
        db.query(AdmissionCriteria)
        .filter(
            AdmissionCriteria.year == req.target_year,
            AdmissionCriteria.benchmark_score <= effective_score,
        )
    )
    if req.student_group_code:
        crit_query = crit_query.filter(
            (AdmissionCriteria.group_code == req.student_group_code)
            | (AdmissionCriteria.group_code.is_(None))
        )
    criteria_list = crit_query.all()

    # Lọc tiếp: điểm sàn (minimum_threshold), thể lực, giới tính
    candidate_items: List[RecommendationResultItem] = []
    
    for c in criteria_list:
        # Kiểm tra điểm sàn
        if c.minimum_threshold is not None and effective_score < c.minimum_threshold:
            continue

        # Kiểm tra giới tính
        if c.gender_requirement and c.gender_requirement != "Any":
            if req.student_gender != c.gender_requirement:
                continue

        # Kiểm tra chiều cao
        warning_msg = None
        if req.student_gender == "Male" and c.min_height_male is not None:
            if req.student_height is not None and req.student_height < c.min_height_male:
                continue
            if req.student_height is None:
                warning_msg = f"Ngành yêu cầu chiều cao nam tối thiểu {c.min_height_male}cm. Bạn chưa cập nhật chiều cao."

        if req.student_gender == "Female" and c.min_height_female is not None:
            if req.student_height is not None and req.student_height < c.min_height_female:
                continue
            if req.student_height is None:
                warning_msg = f"Ngành yêu cầu chiều cao nữ tối thiểu {c.min_height_female}cm. Bạn chưa cập nhật chiều cao."

        # Kiểm tra độ cận
        if c.max_eye_degree is not None:
            if req.student_eye_degree is not None and req.student_eye_degree > c.max_eye_degree:
                continue
            if req.student_eye_degree is None:
                warning_msg = f"Ngành yêu cầu độ cận tối đa {c.max_eye_degree} đi-ốp. Bạn chưa cập nhật thị lực."

        # Kiểm tra chương trình
        prog = db.query(Program).filter(Program.program_id == c.program_id).first()
        if not prog or prog.uni_id not in unis:
            continue

        # Ràng buộc ngân sách học phí thực tế
        if prog.effective_cost > req.max_annual_budget:
            continue

        uni = unis[prog.uni_id]
        career = db.query(Career).filter(Career.career_id == prog.career_id).first() if prog.career_id else None

        # Tính độ khớp Holland RIASEC
        holland_match = 0.7  # Điểm cơ sở
        career_name = "Chuyên viên khối ngành " + prog.name
        job_growth = 8.5
        top_companies = ["Các doanh nghiệp hàng đầu"]
        
        if career:
            career_name = career.title
            job_growth = career.job_growth_rate
            top_companies = career.top_companies or []
            codes = career.holland_codes or []
            if holland_code in codes:
                holland_match = 1.0
            elif any(primary_holland in cd for cd in codes):
                holland_match = 0.85
            else:
                holland_match = 0.65

        margin = round(effective_score - (c.benchmark_score or 0.0), 2)
        if margin >= 1.5:
            safety = "Safe"
        elif margin >= 0.0:
            safety = "Target"
        else:
            safety = "Reach"

        candidate_items.append(
            RecommendationResultItem(
                university_id=uni.uni_id,
                university_name=uni.name,
                university_short_name=uni.short_name,
                faculty_ratio=prog.faculty_ratio,
                facilities=prog.facilities or [],
                program_id=prog.program_id,
                program_name=prog.name,
                credential=prog.degree_level or "Cử nhân",
                benchmark_score=c.benchmark_score or 0.0,
                minimum_threshold=c.minimum_threshold,
                group_code=c.group_code or req.student_group_code,
                tie_breaker_subject=c.tie_breaker_subject or "Toán",
                source_url=c.source_url or uni.admissions_url or "https://tuyensinh.edu.vn",
                score_margin=margin,
                official_tuition=prog.tuition_annual,
                is_subsidized=prog.is_subsidized,
                actual_tuition=prog.effective_cost,
                career_name=career_name,
                job_growth_rate=job_growth,
                hiring_companies=top_companies,
                holland_match_score=holland_match,
                city=uni.location,
                transport_score=8,
                safety_level=safety,
                warning=warning_msg,
            )
        )

    # Sắp xếp theo: Độ khớp Holland giảm dần, Mức độ tăng trưởng việc làm giảm dần, và Điểm dôi dư tăng dần
    candidate_items.sort(
        key=lambda x: (x.holland_match_score, x.job_growth_rate, -x.score_margin),
        reverse=True
    )

    limited_results = candidate_items[:limit]
    if not limited_results:
        return _build_empty_response(req)

    return RecommendationResponse(
        total_found=len(limited_results),
        target_year=req.target_year,
        holland_code=holland_code,
        student_group_code=req.student_group_code,
        results=limited_results,
    )


def _build_empty_response(req: RecommendationRequest, reason: Optional[str] = None) -> RecommendationResponse:
    suggestions = [
        "Mức điểm thi hiện tại đang sát ngưỡng điểm chuẩn của các trường trong bộ lọc. Bạn có thể cân nhắc thêm các trường công lập khu vực địa phương.",
        "Ngân sách học phí hiện tại có thể giới hạn các chương trình đào tạo quốc tế hoặc tự chủ tài chính. Bạn có thể tìm kiếm các ngành được hỗ trợ học phí theo Nghị định 116 (như Sư phạm) hoặc các trường có quỹ học bổng lớn.",
        "Thử nới lỏng hoặc bỏ lọc Tỉnh/Thành phố ưu tiên để xem các chương trình đào tạo uy tín tại các trung tâm giáo dục khác.",
        "Cân nhắc các phương thức xét tuyển khác như Đánh giá năng lực (V-ACT/HSA) hoặc xét học bạ kết hợp chứng chỉ ngoại ngữ."
    ]
    return RecommendationResponse(
        total_found=0,
        target_year=req.target_year,
        holland_code=req.holland_code,
        student_group_code=req.student_group_code,
        results=[],
        empty_suggestions=suggestions
    )

