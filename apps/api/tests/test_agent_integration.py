"""
Integration Tests for Conversational LangGraph Agent in For Your Future.
Tests Intent Classification, Slot Merging, Clarification loop, and Graph Retrieval.
"""

import pytest
from app.agent import (
    career_advisory_service,
    AgentState,
    classify_intent,
    extract_slots_from_prompt,
    merge_slots,
    check_missing_slots
)


def test_slot_extraction_regex():
    """Kiểm tra bóc tách thực thể thô bằng regex"""
    prompt = "Em thi khối A01 được 25.5 điểm muốn học công nghệ thông tin ở TP.HCM học phí tầm 30tr"
    slots = extract_slots_from_prompt(prompt)
    assert slots["student_score"] == 25.5
    assert slots["student_group_code"] == "A01"
    assert slots["preferred_city"] == "TP.HCM"
    assert slots["max_annual_budget"] == 30_000_000


def test_safe_slot_merging():
    """Kiểm tra gộp slot nhiều lượt an toàn (không bị ghi đè None)"""
    slot_turn_1 = {"student_group_code": "A00", "target_major_keywords": ["CNTT"]}
    slot_turn_2 = {"student_score": 26.0}
    merged = merge_slots(slot_turn_1, slot_turn_2)
    assert merged["student_group_code"] == "A00"
    assert merged["student_score"] == 26.0
    assert "CNTT" in merged["target_major_keywords"]


def test_missing_slots_detection():
    """Kiểm tra phát hiện thiếu slot cốt lõi"""
    missing_both = check_missing_slots({})
    assert "student_score" in missing_both
    assert "student_group_code" in missing_both

    missing_group = check_missing_slots({"student_score": 24.0})
    assert "student_group_code" in missing_group
    assert "student_score" not in missing_group

    complete = check_missing_slots({"student_score": 24.0, "student_group_code": "A00"})
    assert len(complete) == 0


@pytest.mark.asyncio
async def test_fast_intent_classification():
    """Kiểm tra phân loại intent bằng rule nhanh"""
    assert await classify_intent("xin chào bạn") == "CHITCHAT"
    assert await classify_intent("so sánh trường Bách khoa và KHTN") == "COMPARE"
    assert await classify_intent("học phí trường IUH là bao nhiêu?") == "LOOKUP"


@pytest.mark.asyncio
async def test_agent_clarification_flow():
    """Kiểm tra flow hỏi lại khi thiếu điểm hoặc khối thi"""
    prompt = "Tư vấn cho em ngành CNTT ở TPHCM"
    events = []
    async for ev in career_advisory_service.run_advisory_flow(prompt=prompt, session_id="test_clarify_turn"):
        events.append(ev)

    clarification_ev = next((e for e in events if e.get("type") == "clarification"), None)
    assert clarification_ev is not None
    assert len(clarification_ev.get("question", "")) > 0


@pytest.mark.asyncio
async def test_agent_full_recommendation_flow():
    """Kiểm tra flow đề xuất hoàn chỉnh khi đã đủ điểm và khối thi"""
    prompt = "Em được 25 điểm khối A01 muốn học ngành Điện - Điện tử hoặc CNTT tại TP.HCM ngân sách 40 triệu"
    events = []
    async for ev in career_advisory_service.run_advisory_flow(prompt=prompt, session_id="test_rec_turn"):
        events.append(ev)

    portfolio_ev = next((e for e in events if e.get("type") == "portfolio"), None)
    assert portfolio_ev is not None
    portfolio_data = portfolio_ev.get("data", {})
    assert "reach" in portfolio_data
    assert "target" in portfolio_data
    assert "safe" in portfolio_data
    assert "all_candidates" in portfolio_data


def test_api_chat_recommend_endpoint():
    """Kiểm tra gọi trực tiếp API /api/v1/chat/recommend nhận JSON"""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/chat/recommend",
        json={"prompt": "Em 25 điểm khối A01 muốn học ngành Điện - Điện tử ở TP.HCM"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "portfolio" in data or "advice" in data or "clarification_question" in data
