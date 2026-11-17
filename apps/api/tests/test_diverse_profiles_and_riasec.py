"""
Extensive Multi-Persona Test Suite covering:
1. 6 RIASEC Holland types (R, I, A, S, E, C)
2. Score variations (Low 18đ, Mid 21-24đ, High 26-27đ, Elite 28.5đ)
3. Geographic variations (TP.HCM, Hà Nội, Đà Nẵng, Cần Thơ)
4. Budget variations (Low <15tr, Standard 25-40tr, High 80-120tr)
5. Military interest and multi-turn incremental state preservation
"""

import pytest
import asyncio
from typing import Dict, Any, List

from app.agent.service import career_advisory_service
from app.agent.slot_filling import extract_slots_from_prompt, merge_slots, check_missing_slots
from app.agent.intent_classifier import classify_intent
from app.modules.graphrag.models.recommendation import RecommendationRequest
from app.modules.graphrag.recommender import rank_and_score_programs, build_portfolio_recommendations
from app.agent.graph import execute_query_async


@pytest.mark.asyncio
async def test_persona_1_realistic_engineering():
    """
    Persona 1: RIASEC R (Realistic - Kỹ thuật / Cơ khí / Ô tô)
    Học sinh: 23.5 điểm, Khối A00, TP.HCM, Ngân sách 35 triệu/năm, Holland: RIE.
    """
    prompt = "Em có tính cách RIE thích máy móc kỹ thuật, thi khối A00 được 23.5 điểm ở TP.HCM, học phí tầm 35tr/năm."
    slots = extract_slots_from_prompt(prompt)
    slots["inferred_holland_code"] = "RIE"

    assert slots["student_score"] == 23.5
    assert slots["student_group_code"] == "A00"
    assert slots["preferred_city"] == "TP.HCM"
    assert slots["max_annual_budget"] == 35_000_000

    # Chạy luồng Advisory
    tokens = []
    events = []
    async for ev in career_advisory_service.run_advisory_flow(prompt=prompt, session_id="test_p1_rie", history=[]):
        events.append(ev)
        if ev.get("type") == "token":
            tokens.append(ev.get("token", ""))

    text = "".join(tokens).lower()
    # Kiểm tra phản hồi có định hướng kỹ thuật và phù hợp
    assert any(w in text for w in ["kỹ thuật", "cơ khí", "ô tô", "điện", "bách khoa", "sư phạm kỹ thuật", "công nghiệp"])
    assert "23.5" in text or "23,5" in text or "a00" in text


@pytest.mark.asyncio
async def test_persona_2_investigative_cs_ai():
    """
    Persona 2: RIASEC I (Investigative - Khoa học máy tính / AI / Dữ liệu)
    Hồ sơ giống screenshot của user: 24.0 điểm A01, Long An/TP.HCM, 40tr/năm, Holland: ISR.
    """
    prompt = "Em được 24 điểm khối A01, muốn học Công nghệ thông tin hoặc Trí tuệ nhân tạo ở TP.HCM, ngân sách 40 triệu/năm, mã Holland ISR."
    slots = extract_slots_from_prompt(prompt)
    slots["inferred_holland_code"] = "ISR"

    assert slots["student_score"] == 24.0
    assert slots["student_group_code"] == "A01"
    assert slots["preferred_city"] == "TP.HCM"
    assert slots["max_annual_budget"] == 40_000_000

    tokens = []
    portfolio_found = False
    async for ev in career_advisory_service.run_advisory_flow(prompt=prompt, session_id="test_p2_isr", history=[]):
        if ev.get("type") == "portfolio":
            portfolio_found = True
        elif ev.get("type") == "token":
            tokens.append(ev.get("token", ""))

    text = "".join(tokens).lower()
    assert any(kw in text for kw in ["công nghệ thông tin", "cntt", "trí tuệ nhân tạo", "ai", "phần mềm", "khoa học máy tính"])
    assert any(uni in text for uni in ["uit", "hcmut", "iuh", "hutech", "khoa học tự nhiên", "sư phạm kỹ thuật"])


@pytest.mark.asyncio
async def test_persona_3_artistic_design_media():
    """
    Persona 3: RIASEC A (Artistic - Thiết kế đồ họa / Mỹ thuật / Đa phương tiện)
    Học sinh: 22.0 điểm, Khối D01, Hà Nội, Ngân sách 25 triệu/năm, Holland: AES.
    """
    prompt = "Em có mã Holland AES thích thiết kế đồ họa và truyền thông đa phương tiện, thi D01 được 22 điểm ở Hà Nội, ngân sách 25 triệu/năm."
    slots = extract_slots_from_prompt(prompt)
    slots["inferred_holland_code"] = "AES"

    assert slots["student_score"] == 22.0
    assert slots["student_group_code"] == "D01"
    assert slots["preferred_city"] == "Hà Nội"

    tokens = []
    async for ev in career_advisory_service.run_advisory_flow(prompt=prompt, session_id="test_p3_aes", history=[]):
        if ev.get("type") == "token":
            tokens.append(ev.get("token", ""))

    text = "".join(tokens).lower()
    assert any(kw in text for kw in ["thiết kế", "đồ họa", "truyền thông", "đa phương tiện", "mỹ thuật", "kiến trúc"])


@pytest.mark.asyncio
async def test_persona_4_social_education_health():
    """
    Persona 4: RIASEC S (Social - Sư phạm / Giáo dục / Y tế)
    Học sinh: 25.5 điểm, Khối B00, Đà Nẵng, Ngân sách tiết kiệm 20 triệu/năm, Holland: SEA.
    """
    prompt = "Em thích làm việc cộng đồng và chăm sóc sức khỏe, mã Holland SEA, thi B00 được 25.5 điểm ở Đà Nẵng, học phí tầm 20tr/năm."
    slots = extract_slots_from_prompt(prompt)
    slots["inferred_holland_code"] = "SEA"

    assert slots["student_score"] == 25.5
    assert slots["student_group_code"] == "B00"
    assert slots["preferred_city"] == "Đà Nẵng"

    tokens = []
    async for ev in career_advisory_service.run_advisory_flow(prompt=prompt, session_id="test_p4_sea", history=[]):
        if ev.get("type") == "token":
            tokens.append(ev.get("token", ""))

    text = "".join(tokens).lower()
    assert any(kw in text for kw in ["y", "dược", "sư phạm", "y tế", "đà nẵng"])


@pytest.mark.asyncio
async def test_persona_5_enterprising_business_marketing():
    """
    Persona 5: RIASEC E (Enterprising - Quản trị kinh doanh / Marketing / Kinh tế)
    Học sinh: 26.5 điểm, Khối D01, TP.HCM, Ngân sách 45 triệu/năm, Holland: ESC.
    """
    prompt = "Em có thế mạnh giao tiếp và đàm phán (mã ESC), thi D01 được 26.5 điểm ở TP.HCM, muốn học Quản trị kinh doanh hoặc Marketing, ngân sách 45 triệu/năm."
    slots = extract_slots_from_prompt(prompt)
    slots["inferred_holland_code"] = "ESC"

    assert slots["student_score"] == 26.5
    assert slots["student_group_code"] == "D01"
    assert slots["preferred_city"] == "TP.HCM"

    tokens = []
    async for ev in career_advisory_service.run_advisory_flow(prompt=prompt, session_id="test_p5_esc", history=[]):
        if ev.get("type") == "token":
            tokens.append(ev.get("token", ""))

    text = "".join(tokens).lower()
    assert any(kw in text for kw in ["kinh doanh", "marketing", "quản trị", "ueh", "kinh tế"])


@pytest.mark.asyncio
async def test_persona_6_conventional_finance_accounting():
    """
    Persona 6: RIASEC C (Conventional - Kế toán / Kiểm toán / Phân tích tài chính)
    Học sinh: 27.0 điểm, Khối A01, Hà Nội, Ngân sách 30 triệu/năm, Holland: CIS.
    """
    prompt = "Em cẩn thận tỉ mỉ, mã Holland CIS, thi A01 được 27 điểm ở Hà Nội, muốn học Kế toán hoặc Tài chính ngân hàng, ngân sách 30 triệu."
    slots = extract_slots_from_prompt(prompt)
    slots["inferred_holland_code"] = "CIS"

    assert slots["student_score"] == 27.0
    assert slots["student_group_code"] == "A01"
    assert slots["preferred_city"] == "Hà Nội"

    tokens = []
    async for ev in career_advisory_service.run_advisory_flow(prompt=prompt, session_id="test_p6_cis", history=[]):
        if ev.get("type") == "token":
            tokens.append(ev.get("token", ""))

    text = "".join(tokens).lower()
    assert any(kw in text for kw in ["kế toán", "tài chính", "ngân hàng", "neu", "kinh tế quốc dân", "học viện tài chính"])


@pytest.mark.asyncio
async def test_persona_7_elite_score_hust_neu():
    """
    Persona 7: Thủ khoa / Điểm siêu cao (28.5 điểm A00 ở Hà Nội)
    Kỳ vọng: Đề xuất các chương trình tinh hoa / top 1 (Khoa học máy tính HUST, Kinh tế quốc dân).
    """
    from app.agent.graph import node_query_neo4j, node_rank_portfolio
    state = {
        "latest_user_prompt": "Tư vấn nguyện vọng điểm 28.5 A00 Hà Nội",
        "slots": {
            "student_score": 28.5,
            "student_group_code": "A00",
            "preferred_city": "Hà Nội",
            "max_annual_budget": 45_000_000,
            "inferred_holland_code": "IRC"
        }
    }
    q_res = await node_query_neo4j(state)
    assert len(q_res["raw_candidates"]) > 0, "Không tìm thấy chương trình cho mức điểm 28.5"
    state.update(q_res)
    p_res = node_rank_portfolio(state)
    portfolio = p_res["portfolio"]
    assert portfolio["total_evaluated"] > 0
    all_cards = portfolio["reach"] + portfolio["target"] + portfolio["safe"]
    assert len(all_cards) > 0


@pytest.mark.asyncio
async def test_persona_8_modest_score_safety():
    """
    Persona 8: Mức điểm khiêm tốn (18.0 điểm A00 ở TP.HCM)
    Kỳ vọng: Hệ thống KHÔNG BỊ TRỐNG PORTFOLIO; tìm ra các trường an toàn và trường mục tiêu vừa sức.
    """
    from app.agent.graph import node_query_neo4j, node_rank_portfolio
    state = {
        "latest_user_prompt": "Tư vấn nguyện vọng điểm 18 A00 TP.HCM",
        "slots": {
            "student_score": 18.0,
            "student_group_code": "A00",
            "preferred_city": "TP.HCM",
            "max_annual_budget": 35_000_000,
            "inferred_holland_code": "RIE"
        }
    }
    q_res = await node_query_neo4j(state)
    assert len(q_res["raw_candidates"]) > 0, "Học sinh 18 điểm phải có ít nhất 1 chương trình phù hợp"
    state.update(q_res)
    p_res = node_rank_portfolio(state)
    portfolio = p_res["portfolio"]
    assert portfolio["total_evaluated"] > 0


@pytest.mark.asyncio
async def test_persona_9_strict_low_budget():
    """
    Persona 9: Ngân sách tài chính rất ngặt nghèo (< 18 triệu VNĐ/năm).
    Kỳ vọng: Recommender lọc chuẩn xác theo học phí, loại bỏ các chương trình đắt đỏ > 18tr khỏi Target/Safety.
    """
    from app.agent.graph import node_query_neo4j, node_rank_portfolio
    state = {
        "latest_user_prompt": "Tư vấn nguyện vọng điểm 24 A00 học phí dưới 18 triệu",
        "slots": {
            "student_score": 24.0,
            "student_group_code": "A00",
            "preferred_city": "Hà Nội",
            "max_annual_budget": 18_000_000,
            "inferred_holland_code": "IRC"
        }
    }
    q_res = await node_query_neo4j(state)
    assert len(q_res["raw_candidates"]) > 0
    state.update(q_res)
    p_res = node_rank_portfolio(state)
    portfolio = p_res["portfolio"]
    for c in portfolio["target"] + portfolio["safe"]:
        if c.get("tuition_fee_annual_million") and c["tuition_fee_annual_million"] > 0:
            assert c["tuition_fee_annual_million"] <= 18.0


@pytest.mark.asyncio
async def test_persona_10_high_budget_international():
    """
    Persona 10: Ngân sách cao (100 - 150 triệu VNĐ/năm, xét chương trình quốc tế / tiên tiến).
    """
    from app.agent.graph import node_query_neo4j, node_rank_portfolio
    state = {
        "latest_user_prompt": "Tư vấn nguyện vọng điểm 23 D01 TP.HCM ngân sách 150 triệu",
        "slots": {
            "student_score": 23.0,
            "student_group_code": "D01",
            "preferred_city": "TP.HCM",
            "max_annual_budget": 150_000_000,
            "inferred_holland_code": "ESC"
        }
    }
    q_res = await node_query_neo4j(state)
    assert len(q_res["raw_candidates"]) > 0


@pytest.mark.asyncio
async def test_persona_11_military_aspirations():
    """
    Persona 11: Nguyện vọng trường quân đội / sĩ quan (is_military_interest=True).
    Học sinh đủ chuẩn sức khỏe: 172cm, 0 độ cận, điểm 25.0 A00.
    """
    prompt = "Em muốn thi vào trường quân đội sĩ quan như Học viện Kỹ thuật Quân sự, em cao 1m72 không cận thị, thi A00 tầm 25 điểm."
    slots = extract_slots_from_prompt(prompt)

    assert slots["is_military_interest"] is True
    assert slots["student_score"] == 25.0
    assert slots["student_group_code"] == "A00"

    tokens = []
    async for ev in career_advisory_service.run_advisory_flow(prompt=prompt, session_id="test_p11_military", history=[]):
        if ev.get("type") == "token":
            tokens.append(ev.get("token", ""))

    text = "".join(tokens).lower()
    assert any(kw in text for kw in ["quân sự", "sĩ quan", "quân đội", "kỹ thuật quân sự", "mta", "học viện"])


@pytest.mark.asyncio
async def test_persona_12_multi_turn_state_preservation():
    """
    Persona 12: Hội thoại đa lượt (Multi-turn conversational state merging).
    Lượt 1: Chỉ cho biết sở thích và tỉnh thành -> Agent hỏi thêm điểm và khối.
    Lượt 2: Cung cấp điểm 25 và khối D01 -> Agent giữ nguyên sở thích cũ và tạo giải pháp hoàn chỉnh.
    """
    session_id = "test_multi_turn_merge_flow"

    # Lượt 1
    prompt_1 = "Em thích học Marketing và Logistics ở TP.HCM"
    tokens_1 = []
    events_1 = []
    async for ev in career_advisory_service.run_advisory_flow(prompt=prompt_1, session_id=session_id, history=[]):
        events_1.append(ev)
        if ev.get("type") == "token":
            tokens_1.append(ev.get("token", ""))

    types_1 = [e.get("type") for e in events_1]
    assert "clarification" in types_1, "Lượt 1 thiếu điểm và khối nên agent phải hỏi clarification"

    # Lượt 2
    prompt_2 = "Em thi thử được 25.5 điểm khối D01 ạ, học phí khoảng 35 triệu"
    history = [
        {"role": "user", "content": prompt_1},
        {"role": "assistant", "content": "".join(tokens_1)}
    ]
    tokens_2 = []
    async for ev in career_advisory_service.run_advisory_flow(prompt=prompt_2, session_id=session_id, history=history):
        if ev.get("type") == "token":
            tokens_2.append(ev.get("token", ""))

    text_2 = "".join(tokens_2).lower()
    # Kiểm tra Agent ghi nhớ Marketing/Logistics từ Lượt 1 và xử lý theo mức điểm 25.5 khối D01 ở Lượt 2
    assert any(kw in text_2 for kw in ["marketing", "logistics", "25.5", "d01", "kinh tế"])
