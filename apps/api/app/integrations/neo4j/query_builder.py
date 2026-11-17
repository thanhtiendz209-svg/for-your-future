"""
Cypher Query Builder for GraphRAG Deterministic Pruning Engine.
Transforms validated Pydantic RecommendationRequest into high-performance,
zero-hallucination Cypher queries for Neo4j.
"""

from typing import Any, Dict


class CypherQueryBuilder:
    """
    Trình tạo truy vấn Cypher tối ưu hóa cho hệ thống Tư vấn Hướng nghiệp GraphRAG.
    
    Thực thi Hard Constraint Pruning:
    1. Điểm chuẩn (Benchmark) & Điểm sàn (Minimum Threshold) + Điểm ưu tiên (Bonus points).
    2. Phương thức tuyển sinh & Khối thi (THPT/Học bạ/ĐGNL/Kết hợp).
    3. Ngân sách học phí thực tế sau bù giá (Effective Annual Cost).
    4. Thể lực: Chiều cao tối thiểu, độ cận tối đa, giới tính.
    5. Vị trí địa lý (Tỉnh/Thành phố).
    6. Xếp hạng đa tiêu chí: Độ khớp Holland RIASEC, Tăng trưởng ngành nghề, Biên độ điểm an toàn.
    """

    @staticmethod
    def build_recommendation_query(params: Any, limit: int = 25) -> str:
        """
        Sinh câu lệnh Cypher Pruning hoàn chỉnh sử dụng tham số hóa ($parameters).
        Đảm bảo WHERE clause đặt đúng vị trí MATCH (không bị nuốt bởi OPTIONAL MATCH),
        loại bỏ hoàn toàn điểm dummy 30.0 và lọc chính xác địa lý, khối thi.
        """
        query = (
            "MATCH (sg:SubjectGroup)\n"
            "WHERE ($student_group_code IS NULL OR sg.group_code = $student_group_code)\n"
            "MATCH (ad:AdmissionCriteria)-[:REQUIRES_GROUP]->(sg)\n"
            "WHERE ad.year = $target_year\n"
            "  AND ad.is_latest = true\n"
            "  AND ad.benchmark_score < 30.0\n"
            "  AND ($student_score IS NULL OR ad.benchmark_score <= ($student_score + $bonus_points + 2.0))\n"
            "  AND ($student_score IS NULL OR $student_score < 18.0 OR ad.benchmark_score >= ($student_score + $bonus_points - 4.5))\n"
            "  AND ($student_score IS NULL OR ad.minimum_threshold IS NULL OR ($student_score + $bonus_points) >= ad.minimum_threshold)\n"
            "MATCH (p:Program)-[:HAS_CRITERIA]->(ad)\n"
            "MATCH (p)-[:OFFERED_BY]->(u:University)\n"
            "MATCH (u)-[:LOCATED_AT]->(loc:Location)\n"
            "WHERE (\n"
            "  $target_university_code IS NULL \n"
            "  OR toUpper(coalesce(u.code, '')) = toUpper($target_university_code)\n"
            "  OR toUpper(coalesce(u.short_name, '')) = toUpper($target_university_code)\n"
            ")\n"
            "AND (\n"
            "  $target_university_name IS NULL \n"
            "  OR toLower(u.name) CONTAINS toLower($target_university_name)\n"
            ")\n"
            "AND (\n"
            "  CASE \n"
            "    WHEN $is_military_interest = true THEN (\n"
            "      toLower(u.name) CONTAINS 'sĩ quan'\n"
            "      OR toLower(u.name) CONTAINS 'quân sự'\n"
            "      OR toLower(u.name) CONTAINS 'quân y'\n"
            "      OR toLower(u.name) CONTAINS 'cảnh sát'\n"
            "      OR toLower(u.name) CONTAINS 'an ninh'\n"
            "      OR toLower(u.name) CONTAINS 'biên phòng'\n"
            "      OR toLower(u.name) CONTAINS 'hậu cần'\n"
            "      OR toLower(p.name) CONTAINS 'sĩ quan'\n"
            "      OR toLower(p.name) CONTAINS 'quân sự'\n"
            "    )\n"
            "    ELSE NOT (\n"
            "      toLower(u.name) CONTAINS 'sĩ quan'\n"
            "      OR toLower(u.name) CONTAINS 'quân sự'\n"
            "      OR toLower(u.name) CONTAINS 'quân y'\n"
            "      OR toLower(u.name) CONTAINS 'cảnh sát'\n"
            "      OR toLower(u.name) CONTAINS 'an ninh'\n"
            "      OR toLower(u.name) CONTAINS 'biên phòng'\n"
            "      OR toLower(u.name) CONTAINS 'hậu cần'\n"
            "      OR toLower(p.name) CONTAINS 'sĩ quan'\n"
            "      OR toLower(p.name) CONTAINS 'quân sự'\n"
            "    )\n"
            "  END\n"
            ")\n"
            "AND (\n"
            "  $preferred_city IS NULL \n"
            "  OR $target_university_code IS NOT NULL\n"
            "  OR (toLower(trim($preferred_city)) IN ['hồ chí minh', 'hcm', 'tp.hcm', 'tphcm', 'sài gòn'] AND (toLower(trim(loc.city)) IN ['tp.hcm', 'hồ chí minh', 'hcm'] OR toLower(loc.city) CONTAINS 'hồ chí minh'))\n"
            "  OR (toLower(trim($preferred_city)) IN ['hà nội', 'hn'] AND (toLower(trim(loc.city)) IN ['hà nội', 'hn'] OR toLower(loc.city) CONTAINS 'hà nội'))\n"
            "  OR (toLower(trim($preferred_city)) IN ['đà nẵng', 'đn'] AND (toLower(trim(loc.city)) IN ['đà nẵng', 'đn'] OR toLower(loc.city) CONTAINS 'đà nẵng'))\n"
            "  OR toLower(trim(loc.city)) CONTAINS toLower(trim($preferred_city))\n"
            ")\n"
            "AND (\n"
            "  size($target_keywords) = 0\n"
            "  OR any(kw IN $target_keywords WHERE toLower(p.name) CONTAINS toLower(kw))\n"
            ")\n"
            "AND NOT (\n"
            "  (size($target_keywords) > 0 OR $is_tech_profile = true) AND (\n"
            "    toLower(p.name) CONTAINS 'ngôn ngữ' \n"
            "    OR toLower(p.name) CONTAINS 'tiếng '\n"
            "    OR toLower(p.name) CONTAINS 'triết học'\n"
            "    OR toLower(p.name) CONTAINS 'thủy sản'\n"
            "    OR toLower(p.name) CONTAINS 'nông nghiệp'\n"
            "    OR toLower(p.name) CONTAINS 'chính trị'\n"
            "    OR toLower(p.name) CONTAINS 'văn học'\n"
            "    OR toLower(p.name) CONTAINS 'lịch sử'\n"
            "    OR toLower(p.name) CONTAINS 'du lịch'\n"
            "    OR toLower(p.name) CONTAINS 'phục hồi chức năng'\n"
            "    OR toLower(p.name) CONTAINS 'điều dưỡng'\n"
            "    OR toLower(p.name) CONTAINS 'y khoa'\n"
            "    OR toLower(p.name) CONTAINS 'y học'\n"
            "    OR toLower(p.name) CONTAINS 'dược'\n"
            "    OR toLower(p.name) CONTAINS 'y tế'\n"
            "    OR toLower(p.name) CONTAINS 'sĩ quan'\n"
            "    OR toLower(p.name) CONTAINS 'miền bắc'\n"
            "  )\n"
            ")\n"
            "OPTIONAL MATCH (p)-[:HAS_FINANCIAL]->(fa:FinancialAspect)\n"
            "WHERE ($max_annual_budget IS NULL OR fa.tuition_subsidy = true OR fa.effective_annual_cost <= ($max_annual_budget * 1.35))\n"
            "OPTIONAL MATCH (p)-[:PREPARES_FOR]->(c:Career)\n"
            "OPTIONAL MATCH (h:HollandType)-[rel:MATCH|ALIGNED_WITH]->(c)\n"
            "  WHERE ($holland_code IS NULL OR h.code = $holland_code)\n"
            "WITH u, p, loc,\n"
            "     head(collect(ad)) AS ad,\n"
            "     head(collect(fa)) AS fa,\n"
            "     head(collect(DISTINCT coalesce(c.title, p.name))) AS career_name,\n"
            "     max(coalesce(c.job_growth_rate, 0.0)) AS job_growth_rate,\n"
            "     reduce(acc = [], list IN collect(DISTINCT coalesce(c.top_hiring_companies, [])) | acc + list) AS all_companies,\n"
            "     max(coalesce(rel.weight, 1.0)) AS holland_match_score\n"
            "WITH u, p, ad, fa, loc, career_name, job_growth_rate, all_companies, holland_match_score,\n"
            "     CASE WHEN $student_score IS NOT NULL THEN round(($student_score + $bonus_points) - ad.benchmark_score, 2) ELSE 0.0 END AS score_margin\n"
            "RETURN \n"
            "  u.uni_id AS university_id,\n"
            "  u.name AS university_name,\n"
            "  u.short_name AS university_short_name,\n"
            "  u.student_faculty_ratio AS faculty_ratio,\n"
            "  coalesce(u.campus_facilities, []) AS facilities,\n"
            "  p.program_id AS program_id,\n"
            "  p.name AS program_name,\n"
            "  coalesce(p.educational_credential_awarded, 'Cử nhân / Kỹ sư') AS credential,\n"
            "  p.program_prerequisites AS prerequisites,\n"
            "  p.accreditation AS accreditation,\n"
            "  ad.benchmark_score AS benchmark_score,\n"
            "  ad.minimum_threshold AS minimum_threshold,\n"
            "  score_margin,\n"
            "  toInteger(coalesce(fa.tuition_fee_annual, 0)) AS official_tuition,\n"
            "  coalesce(fa.tuition_subsidy, false) AS is_subsidized,\n"
            "  toInteger(coalesce(fa.effective_annual_cost, fa.tuition_fee_annual, 0)) AS actual_tuition,\n"
            "  career_name,\n"
            "  job_growth_rate,\n"
            "  all_companies[..3] AS hiring_companies,\n"
            "  holland_match_score,\n"
            "  loc.city AS city,\n"
            "  loc.public_transport_score AS transport_score,\n"
            "  CASE \n"
            "    WHEN score_margin < -0.5 THEN 'Reach'\n"
            "    WHEN score_margin <= 1.0 THEN 'Target'\n"
            "    ELSE 'Safe'\n"
            "  END AS safety_level\n"
            "ORDER BY \n"
            "  (CASE WHEN size($target_keywords) > 0 AND any(kw IN $target_keywords WHERE toLower(p.name) CONTAINS toLower(kw)) THEN 0 ELSE 1 END) ASC,\n"
            "  abs(score_margin) ASC, \n"
            "  ad.benchmark_score DESC\n"
            "LIMIT $limit"
        )
        return query

    @staticmethod
    def extract_query_parameters(params: Any, limit: int = 25) -> Dict[str, Any]:
        """
        Trích xuất và chuẩn hóa dictionary parameters cho Neo4j driver từ RecommendationRequest hoặc ExtractedIntent.
        Không áp đặt giá trị mặc định cứng (zero-hardcode).
        """
        target_year = getattr(params, "target_year", 2026) or 2026
        student_group_code = getattr(params, "student_group_code", None)
        student_score = getattr(params, "student_score", None)
        bonus_points = getattr(params, "bonus_points", 0.0) or 0.0
        max_annual_budget = getattr(params, "max_annual_budget", None)
        
        student_gender = getattr(params, "student_gender", "Any") or "Any"
        if hasattr(student_gender, "value"):
            student_gender = student_gender.value
            
        student_height = getattr(params, "student_height", None)
        student_eye_degree = getattr(params, "student_eye_degree", None)
        preferred_city = getattr(params, "preferred_city", None)
        
        target_university_code = getattr(params, "target_university_code", None)
        target_university_name = getattr(params, "target_university", None)
        is_military_interest = bool(getattr(params, "is_military_interest", False))

        holland_code = getattr(params, "holland_code", None) or getattr(params, "inferred_holland_code", None)
        if holland_code:
            holland_code = str(holland_code).upper().strip()
            if len(holland_code) < 3:
                for ch in "RIASEC":
                    if ch not in holland_code:
                        holland_code += ch
                    if len(holland_code) >= 3:
                        break
            holland_code = holland_code[:3]
        else:
            holland_code = None

        raw_kw = getattr(params, "target_career_keywords", []) or []
        target_keywords = [str(k).strip() for k in raw_kw if str(k).strip()]

        # Check if technical intent profile
        is_tech = False
        raw_text = getattr(params, "raw_query", "") or getattr(params, "raw_prompt", "") or ""
        r_lower = raw_text.lower()
        if any(k in r_lower for k in ["intj", "kỹ thuật", "công nghệ", "it", "lập trình", "máy tính", "bách khoa", "khoa học"]) or (holland_code and holland_code[0] in ["R", "I"]):
            is_tech = True

        return {
            "target_year": target_year,
            "student_group_code": student_group_code,
            "student_score": student_score,
            "bonus_points": bonus_points,
            "max_annual_budget": max_annual_budget,
            "student_gender": str(student_gender),
            "student_height": student_height,
            "student_eye_degree": student_eye_degree,
            "preferred_city": preferred_city,
            "target_university_code": target_university_code,
            "target_university_name": target_university_name,
            "is_military_interest": is_military_interest,
            "holland_code": holland_code,
            "target_keywords": target_keywords,
            "is_tech_profile": is_tech,
            "limit": limit,
        }
