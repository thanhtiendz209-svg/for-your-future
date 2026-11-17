"""
Comprehensive Domain Coverage Tests for GraphRAG Advisory Agent.
Tests across diverse:
1. Universities (North, Central, South: HUST, HCMUT, PTIT, NEU, FTU, UIT, DUT, UEH)
2. Specific Programs at Universities (CNTT, Khoa học máy tính, Logistics, Quản trị kinh doanh)
3. Careers (Công nghệ thông tin, Thiết kế, Marketing, Logistics, Kinh tế)
4. Job Positions & Dải lương CareerViet (AI Engineer, UI/UX Designer, Software Engineer, Data Analyst)
"""

import pytest
import asyncio
from typing import Dict, Any, List

from app.agent.graph import node_lookup_info, execute_query_async
from app.agent.slot_filling import extract_slots_from_prompt, merge_slots
from app.agent.intent_classifier import classify_intent
from app.agent.service import career_advisory_service


@pytest.mark.asyncio
async def test_all_major_universities_lookup():
    """Kiểm tra tra cứu các trường đại học ở cả 3 miền Bắc - Trung - Nam."""
    test_cases = [
        ("Trường Đại học Bách khoa - ĐHQG TP.HCM (HCMUT)", "HCMUT", "Bách khoa - ĐHQG TP.HCM"),
        ("Học viện Công nghệ Bưu chính Viễn thông (PTIT)", "PTIT", "Bưu chính Viễn thông"),
        ("Đại học Bách khoa Hà Nội (HUST)", "HUST", "Bách khoa Hà Nội"),
        ("Đại học Kinh tế Quốc dân (NEU)", "NEU", "Kinh tế Quốc dân"),
        ("Đại học Ngoại thương (FTU)", "FTU", "Ngoại thương"),
        ("Trường Đại học Công nghệ Thông tin - ĐHQG TP.HCM (UIT)", "UIT", "Công nghệ Thông tin"),
        ("Trường Đại học Bách khoa - Đại học Đà Nẵng (DUT)", "DUT", "Bách khoa - Đại học Đà Nẵng"),
        ("Đại học Kinh tế TP.HCM (UEH)", "UEH", "Kinh tế TP.HCM"),
        ("Trường Đại học Công nghiệp TP.HCM (IUH)", "IUH", "Công nghiệp TP.HCM")
    ]

    for uni_name, uni_code, expected_label in test_cases:
        cypher_uni = """
        MATCH (u:University)
        WHERE ($code <> '' AND (toUpper(coalesce(u.short_name, '')) = toUpper($code) OR toUpper(coalesce(u.uni_id, '')) = toUpper($code) OR toUpper(coalesce(u.code, '')) = toUpper($code)))
           OR ($name <> '' AND toLower(u.name) CONTAINS toLower($name))
           OR ($name <> '' AND toLower($name) CONTAINS toLower(u.name))
           OR ($code <> '' AND toLower(u.name) CONTAINS toLower($code))
        OPTIONAL MATCH (u)-[:LOCATED_AT]->(loc:Location)
        OPTIONAL MATCH (p:Program)-[:OFFERED_BY]->(u)
        OPTIONAL MATCH (p)-[:HAS_FINANCIAL]->(fa:FinancialAspect)
        WITH u, loc, p, fa
        ORDER BY CASE 
            WHEN $code <> '' AND toUpper(coalesce(u.short_name, u.code, '')) = toUpper($code) THEN 1
            WHEN $name <> '' AND toLower(u.name) = toLower($name) THEN 2
            WHEN $name <> '' AND toLower(u.name) CONTAINS toLower($name) THEN 3
            ELSE 4 
        END ASC
        RETURN u.name AS name, coalesce(u.short_name, u.uni_id, u.code) AS code,
               loc.city AS city, count(DISTINCT p) AS total_programs
        LIMIT 1
        """
        records = await execute_query_async(cypher_uni, {"code": uni_code, "name": uni_name})
        assert len(records) > 0, f"Không tìm thấy trường {uni_code} trong Knowledge Graph"
        matched = records[0]
        assert expected_label.lower() in matched["name"].lower() or uni_code == matched["code"], \
            f"Kỳ vọng {expected_label} nhưng Graph trả về {matched['name']}"


@pytest.mark.asyncio
async def test_specific_programs_at_universities():
    """Kiểm tra phân tích ngành học cụ thể tại trường (Program Analysis)."""
    program_tests = [
        {"code": "HCMUT", "keywords": ["Khoa học máy tính"], "expected_uni": "HCMUT"},
        {"code": "FTU", "keywords": ["Logistics"], "expected_uni": "FTU"},
        {"code": "PTIT", "keywords": ["Công nghệ thông tin"], "expected_uni": "PTIT"},
        {"code": "NEU", "keywords": ["Quản trị kinh doanh"], "expected_uni": "NEU"}
    ]

    for pt in program_tests:
        cypher_prog = """
        MATCH (u:University)
        WHERE ($code <> '' AND (toUpper(coalesce(u.short_name, '')) = toUpper($code) OR toUpper(coalesce(u.uni_id, '')) = toUpper($code) OR toUpper(coalesce(u.code, '')) = toUpper($code)))
        WITH u LIMIT 1
        MATCH (p:Program)-[:OFFERED_BY]->(u)
        WHERE any(kw IN $keywords WHERE toLower(p.name) CONTAINS toLower(kw))
        RETURN p.name AS program_name, u.name AS university_name
        LIMIT 5
        """
        records = await execute_query_async(cypher_prog, {
            "code": pt["code"],
            "keywords": pt["keywords"]
        })
        assert len(records) > 0, f"Không tìm thấy ngành {pt['keywords']} tại trường {pt['code']}"
        assert pt["code"] in records[0]["university_name"] or pt["expected_uni"] in records[0]["university_name"]


@pytest.mark.asyncio
async def test_all_10_careers_lookup():
    """Kiểm tra tra cứu 10 nhóm ngành nghề cốt lõi trong Career Knowledge Graph."""
    careers_to_test = [
        "Công nghệ thông tin", "Thiết kế", "Marketing", "Kinh tế", "Kỹ thuật",
        "Giáo dục", "Y tế", "Logistics", "Quản trị", "Khoa học"
    ]

    cypher_career = """
    MATCH (c:Career)
    WHERE toLower(c.title) CONTAINS toLower($query)
       OR any(kw IN $keywords WHERE toLower(c.title) CONTAINS toLower(kw) OR toLower(kw) CONTAINS toLower(c.title))
    OPTIONAL MATCH (c)-[:MAPS]->(j:JobPosition)
    RETURN c.title AS title, c.job_growth_rate AS growth_rate, count(j) AS job_count
    LIMIT 1
    """

    for car in careers_to_test:
        records = await execute_query_async(cypher_career, {
            "query": car,
            "keywords": [car]
        })
        assert len(records) > 0, f"Không tìm thấy nhóm nghề {car} trong Knowledge Graph"
        assert car.lower() in records[0]["title"].lower()
        assert records[0]["growth_rate"] > 0


@pytest.mark.asyncio
async def test_job_positions_and_salaries():
    """Kiểm tra tra cứu các vị trí việc làm và mức lương thực tế từ CareerViet."""
    job_titles = [
        "AI / Machine Learning Engineer",
        "UI/UX Designer",
        "Software Engineer",
        "Data Engineer",
        "Financial Analyst",
        "Digital Marketing"
    ]

    cypher_job = """
    MATCH (j:JobPosition)
    WHERE any(kw IN $keywords WHERE toLower(j.title) CONTAINS toLower(kw))
    RETURN j.title AS title, j.salary_min AS s_min, j.salary_max AS s_max, j.salary_display AS s_display
    LIMIT 1
    """

    for jt in job_titles:
        records = await execute_query_async(cypher_job, {"keywords": [jt.lower()]})
        assert len(records) > 0, f"Không tìm thấy vị trí tuyển dụng '{jt}' trong Graph"
        matched = records[0]
        assert matched["s_min"] > 0
        assert matched["s_max"] >= matched["s_min"]
        assert matched["s_display"] != ""


@pytest.mark.asyncio
async def test_end_to_end_agent_response_accuracy():
    """Kiểm tra end-to-end lời giải đáp của Agent với các prompt về trường và ngành nghề khác nhau."""
    prompts = [
        (
            "Em đang tìm hiểu thông tin về trường Đại học Kinh tế Quốc dân (NEU). Nhờ AI tư vấn học phí và ngành nổi bật.",
            ["kinh tế quốc dân", "neu"]
        ),
        (
            "Em muốn tìm hiểu về nghề Marketing và cơ hội việc làm, mức lương hiện nay thế nào?",
            ["marketing", "lương"]
        )
    ]

    for p, expected_keywords in prompts:
        tokens = []
        async for ev in career_advisory_service.run_advisory_flow(prompt=p, session_id="test_suite", history=[]):
            if ev.get("type") == "token":
                tokens.append(ev.get("token", ""))
        full_text = "".join(tokens).lower()
        for kw in expected_keywords:
            assert kw in full_text, f"Câu trả lời cho '{p}' không chứa từ khóa '{kw}'"
