"""
LangGraph Conversational Career Guidance Agent.
Orchestrates Intent Classification, Slot Filling, Clarification, Neo4j Graph Pruning,
MCDM Portfolio Ranking, and Streaming Response Generation.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import StreamWriter

from .state import AgentState
from .intent_classifier import classify_intent
from .slot_filling import (
    extract_slots_from_prompt,
    extract_slots_with_llm,
    merge_slots,
    check_missing_slots,
    enrich_slots_from_db_profile
)
from .prompts import CLARIFICATION_PROMPT

try:
    from app.integrations.neo4j.client import execute_query_async
    from app.modules.graphrag.models.query_builder import CypherQueryBuilder
    from app.modules.graphrag.models.recommendation import (
        RecommendationRequest,
        RecommendationResultItem,
        ExtractedIntent,
        PortfolioRecommendationResponse
    )
    from app.modules.graphrag.recommender import rank_and_score_programs, build_portfolio_recommendations
    from app.modules.graphrag.llm_service import GeminiStreamInterrupted, stream_gemini_messages
except ImportError:
    try:
        from ..integrations.neo4j.client import execute_query_async
        from ..modules.graphrag.models.query_builder import CypherQueryBuilder
        from ..modules.graphrag.models.recommendation import (
            RecommendationRequest,
            RecommendationResultItem,
            ExtractedIntent,
            PortfolioRecommendationResponse
        )
        from ..modules.graphrag.recommender import rank_and_score_programs, build_portfolio_recommendations
        from ..modules.graphrag.llm_service import GeminiStreamInterrupted, stream_gemini_messages
    except ImportError:
        from database import execute_query_async
        from models.query_builder import CypherQueryBuilder
        from models.recommendation import (
            RecommendationRequest,
            RecommendationResultItem,
            ExtractedIntent,
            PortfolioRecommendationResponse
        )
        from recommender import rank_and_score_programs, build_portfolio_recommendations
        from llm_service import GeminiStreamInterrupted, stream_gemini_messages

logger = logging.getLogger("graphrag.agent.graph")


# =========================================================================
# Node Implementations
# =========================================================================

async def node_classify_intent(state: AgentState) -> Dict[str, Any]:
    """Node 1: Phân loại ý định từ câu prompt gần nhất."""
    prompt = state.get("latest_user_prompt", "")
    messages = state.get("messages", [])
    if not prompt and messages:
        last = messages[-1]
        prompt = getattr(last, "content", None) or (last.get("content") if isinstance(last, dict) else str(last))
    prompt = (prompt or "").strip()
    intent = await classify_intent(prompt, messages)
    logger.info(f"[Agent Graph] Classify Intent -> {intent}")
    return {"intent": intent}


async def node_extract_slots(state: AgentState) -> Dict[str, Any]:
    """Node 2: Trích xuất và Gộp Slots bằng LLM Gemini + DB Profile an toàn."""
    prompt = state.get("latest_user_prompt", "")
    messages = state.get("messages", [])
    if not prompt and messages:
        last = messages[-1]
        prompt = getattr(last, "content", None) or (last.get("content") if isinstance(last, dict) else str(last))
    prompt = (prompt or "").strip()
    existing_slots = state.get("slots", {}) or {}
    messages = state.get("messages", [])

    # Bóc tách slot mới bằng LLM Gemini
    new_extracted = await extract_slots_with_llm(prompt, messages)

    # Gộp an toàn với slot đã lưu ở các lượt trước
    merged = merge_slots(existing_slots, new_extracted)

    # Bổ sung từ profile DB nếu có (ví dụ: điểm thi, khối thi, học phí, địa phương)
    profile_data = state.get("profile_data")
    if profile_data:
        merged = enrich_slots_from_db_profile(merged, profile_data)

    # Kiểm tra thiếu slot
    missing = check_missing_slots(merged)
    logger.info(f"[Agent Graph] Slots merged: score={merged.get('student_score')}, group={merged.get('student_group_code')}, budget={merged.get('max_annual_budget')}, missing={missing}")

    return {
        "slots": merged,
        "missing_slots": missing,
        "clarification_question": None if not missing else state.get("clarification_question")
    }


async def _write_gemini_answer(
    writer: StreamWriter,
    messages: List[Dict[str, str]],
    *,
    temperature: float,
    max_tokens: int,
    fallback: str = "",
    prefer_native: bool = False,
) -> str:
    parts = []
    try:
        async for token in stream_gemini_messages(
            messages, temperature=temperature, max_tokens=max_tokens, prefer_native=prefer_native
        ):
            parts.append(token)
            writer({"type": "token", "token": token})
    except GeminiStreamInterrupted as error:
        if not fallback or error.reason not in ("connection", "busy", "timeout") or "".join(parts).strip():
            raise
        writer({"type": "token", "token": fallback})
        return fallback
    return "".join(parts)


async def node_ask_clarification(state: AgentState, writer: StreamWriter) -> Dict[str, Any]:
    """Node 3: Sinh câu hỏi gợi mở khi thiếu điểm hoặc khối thi."""
    slots = state.get("slots", {})
    missing = state.get("missing_slots", [])

    missing_desc_parts = []
    if "student_score" in missing:
        missing_desc_parts.append("- Điểm thi tốt nghiệp THPT (hoặc điểm thi thử/mục tiêu kỳ vọng)")
    if "student_group_code" in missing:
        missing_desc_parts.append("- Tổ hợp môn / Khối thi dự tuyển (A00, A01, D01, B00, C00...)")

    missing_desc = "\n".join(missing_desc_parts)

    majors = ", ".join(slots.get("target_major_keywords", [])) or "Chưa xác định cụ thể"
    city = slots.get("preferred_city") or "Chưa xác định"
    budget = f"{slots.get('max_annual_budget', 0):,.0f} VND/năm" if slots.get("max_annual_budget") else "Chưa xác định"
    latest_user_prompt = state.get("latest_user_prompt", "")

    prompt = (
        f"{CLARIFICATION_PROMPT.format(missing_info_desc=missing_desc, target_majors=majors, preferred_city=city, budget_info=budget)}\n\n"
        f"Câu nói vừa rồi của học sinh: \"{latest_user_prompt}\""
    )

    if "student_score" in missing and "student_group_code" in missing:
        fallback = "Chào bạn! Bạn cho mình biết điểm thi dự kiến và tổ hợp xét tuyển (ví dụ A00, A01 hoặc D01) để mình tra cứu trường phù hợp nhé!"
    elif "student_score" in missing:
        fallback = f"Bạn đã chọn khối {slots.get('student_group_code')}. Bạn cho mình xin thêm mức điểm thi dự kiến để tra cứu nhé!"
    else:
        fallback = f"Với mức điểm {slots.get('student_score')}, bạn dự định xét tuyển theo tổ hợp nào (ví dụ A00, A01 hoặc D01)?"

    clarify_text = await _write_gemini_answer(
        writer, [{"role": "user", "content": prompt}],
        temperature=0.4, max_tokens=350, fallback=fallback,
        prefer_native=state.get("prefer_native", False),
    )

    return {
        "clarification_question": clarify_text,
        "final_text": clarify_text
    }


async def node_query_neo4j(state: AgentState) -> Dict[str, Any]:
    """Node 4: Thực thi Cypher Pruning trên Knowledge Graph Neo4j."""
    slots = state.get("slots", {})

    score_val = slots.get("student_score")
    student_score = float(score_val) if score_val is not None else None

    group_val = slots.get("student_group_code")
    student_group_code = str(group_val).upper().strip() if group_val else None

    intent = ExtractedIntent(
        raw_query=state.get("latest_user_prompt", ""),
        intent_type=state.get("intent", "RECOMMEND"),
        student_score=student_score,
        bonus_points=float(slots.get("bonus_points", 0.0) or 0.0),
        student_group_code=student_group_code,
        target_career_keywords=slots.get("target_major_keywords", []),
        target_university=slots.get("target_university"),
        target_university_code=slots.get("target_university_code"),
        is_military_interest=bool(slots.get("is_military_interest", False)),
        preferred_city=slots.get("preferred_city"),
        max_annual_budget=slots.get("max_annual_budget"),
        inferred_holland_code=slots.get("inferred_holland_code") or "RIA",
        student_eye_degree=slots.get("student_eye_degree"),
        student_height=slots.get("student_height")
    )
    if intent.inferred_holland_code:
        code = str(intent.inferred_holland_code).upper().strip()
        if len(code) < 3:
            for ch in "RIASEC":
                if ch not in code:
                    code += ch
                if len(code) >= 3:
                    break
        intent.inferred_holland_code = code[:3]

    query = CypherQueryBuilder.build_recommendation_query(intent, limit=100)
    params = CypherQueryBuilder.extract_query_parameters(intent, limit=100)

    records = await execute_query_async(query, params)
    logger.info(f"[Agent Graph] Neo4j retrieved {len(records)} matching programs")

    return {
        "raw_candidates": records,
        "intent_obj": intent.model_dump()
    }


def node_rank_portfolio(state: AgentState) -> Dict[str, Any]:
    """Node 5: Chấm điểm MCDM và Phân bổ Danh mục 3 Tầng (Reach - Target - Safe)."""
    raw_data = state.get("raw_candidates", [])
    raw_candidates = [RecommendationResultItem(**r) if isinstance(r, dict) else r for r in raw_data]

    intent_raw = state.get("intent_obj")
    if isinstance(intent_raw, dict):
        intent = ExtractedIntent(**intent_raw)
    elif isinstance(intent_raw, ExtractedIntent):
        intent = intent_raw
    else:
        slots = state.get("slots", {})
        intent = ExtractedIntent(
            raw_query=state.get("latest_user_prompt", ""),
            student_score=float(slots.get("student_score", 25.0)),
            student_group_code=str(slots.get("student_group_code", "A00")).upper().strip()
        )

    scored_programs = rank_and_score_programs(raw_candidates, intent)
    portfolio = build_portfolio_recommendations(scored_programs, intent, max_per_tier=3)

    def _map_card(p):
        uni_code = getattr(p, "university_short_name", None) or getattr(p, "university_id", "UNI")
        actual_t = getattr(p, "actual_tuition", None) or getattr(p, "official_tuition", None)
        is_sub = getattr(p, "is_subsidized", False)
        
        # Resolve realistic tuition directly from graph data (FinancialAspect)
        if is_sub:
            tuition_mil = 0.0
        elif actual_t and actual_t > 0:
            tuition_mil = round(float(actual_t) / 1_000_000, 1)
        else:
            tuition_mil = None

        hiring = getattr(p, "hiring_companies", []) or getattr(p, "top_jobs_market", [])
        return {
            "university_code": uni_code,
            "university_name": p.university_name,
            "program_name": p.program_name,
            "admission_score": float(p.benchmark_score),
            "score_margin": float(p.score_margin),
            "tuition_fee": tuition_mil,
            "location": getattr(p, "city", "Toàn quốc"),
            "tier": p.portfolio_tier,
            "mcdm_rank_score": float(p.mcdm_score),
            "career_connections": [p.career_name] if getattr(p, "career_name", None) else [],
            "hiring_partners": hiring[:3]
        }

    all_cands = getattr(portfolio, "all_candidates", [])
    portfolio_dict = {
        "total_evaluated": portfolio.total_found,
        "reach": [_map_card(p) for p in portfolio.reach_programs],
        "target": [_map_card(p) for p in portfolio.target_programs],
        "safe": [_map_card(p) for p in portfolio.safe_programs],
        "all_candidates": [_map_card(p) for p in all_cands]
    }

    return {
        "portfolio": portfolio_dict,
        "portfolio_obj": portfolio.model_dump(),
        "clarification_question": None
    }


def node_generate_advice(state: AgentState) -> Dict[str, Any]:
    """Node 6: Đánh dấu trạng thái sẵn sàng cho Stream lời tư vấn AI."""
    return {"final_text": "READY_FOR_PORTFOLIO_STREAM"}


async def node_chitchat(state: AgentState, writer: StreamWriter) -> Dict[str, Any]:
    """Node xử lý Chào hỏi / Hỏi thăm năng lực."""
    prompt = state.get("latest_user_prompt", "")
    messages = [
        {
            "role": "system",
            "content": (
                "Bạn là Cố vấn Tuyển sinh Đại học & Định hướng Nghề nghiệp AI của hệ thống GraphRAG. "
                "Hãy chào bạn học sinh thân thiện, ngắn gọn và nhiệt tình (khoảng 2-3 câu). "
                "Giới thiệu rằng bạn có thể giúp học sinh chọn ngành nghề phù hợp tính cách, tra cứu điểm chuẩn, "
                "học phí thực tế và sắp xếp danh mục nguyện vọng (Reach - Target - Safe) dựa trên Knowledge Graph."
            )
        },
        {"role": "user", "content": prompt}
    ]
    reply = await _write_gemini_answer(
        writer, messages, temperature=0.5, max_tokens=200,
        fallback="Chào bạn! Mình có thể giúp bạn tìm ngành, tra cứu trường và chuẩn bị nguyện vọng. Bạn muốn tìm hiểu điều gì?",
        prefer_native=state.get("prefer_native", False),
    )
    return {"final_text": reply}


async def node_out_of_scope(state: AgentState) -> Dict[str, Any]:
    """Node từ chối khéo các câu hỏi ngoài phạm vi."""
    resp = "Dạ, hiện tại mình là Cố vấn AI chuyên sâu về Tuyển sinh Đại học và Hướng nghiệp. Mình chỉ có thể hỗ trợ bạn về điểm chuẩn, ngành học, học phí và cơ hội việc làm. Bạn có câu hỏi nào về chọn ngành hoặc chọn trường không nè?"
    return {"final_text": resp}


async def node_lookup_info(state: AgentState, writer: StreamWriter) -> Dict[str, Any]:
    """
    Node xử lý Tra cứu chuyên sâu & Tư vấn toàn diện:
    - Tra cứu chi tiết 1 trường đại học (Học phí, ngành nổi bật, môi trường học tập, cơ sở vật chất, ký túc xá).
    - Tra cứu & phân tích 1 ngành nghề (Tiềm năng việc làm, dải lương CareerViet, yêu cầu kỹ năng, top trường đào tạo).
    - Phân tích chi tiết cơ hội xét tuyển & việc làm của 1 ngành cụ thể tại 1 trường cụ thể (Điểm chuẩn, tỷ lệ trúng tuyển với điểm của học sinh).
    - So sánh giữa 2 trường hoặc 2 ngành học.
    - Giải đáp các câu hỏi mở, quy chế tuyển sinh, kỳ thi ĐGNL, phương pháp ôn thi ("prompt lạ ngoài tầm hệ thống").
    """
    prompt = state.get("latest_user_prompt", "")
    slots = state.get("slots", {})
    uni_code = slots.get("target_university_code")
    uni_name = slots.get("target_university")
    major_kws = slots.get("target_major_keywords", [])

    # Thông tin hồ sơ học sinh để cá nhân hoá tư vấn
    student_score = slots.get("student_score")
    student_group = slots.get("student_group_code")
    student_budget = slots.get("max_annual_budget")
    student_city = slots.get("preferred_city")
    holland_code = slots.get("inferred_holland_code")

    lookup_data: Dict[str, Any] = {}

    # 1. Truy vấn thông tin Trường Đại học (nếu có nhắc đến trường)
    if uni_code or uni_name:
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
               loc.city AS city, loc.address AS address, u.type AS type,
               u.website AS website, u.ranking_national AS ranking,
               coalesce(u.has_dormitory, true) AS has_dormitory,
               collect(DISTINCT {name: p.name, code: p.major_code, tuition: fa.tuition_fee_annual})[..15] AS sample_programs,
               count(DISTINCT p) AS total_programs,
               avg(fa.tuition_fee_annual) AS avg_tuition,
               min(fa.tuition_fee_annual) AS min_tuition,
               max(fa.tuition_fee_annual) AS max_tuition
        LIMIT 1
        """
        try:
            records_uni = await execute_query_async(cypher_uni, {"code": uni_code or "", "name": uni_name or ""})
            if records_uni:
                lookup_data["target_university"] = records_uni[0]
        except Exception as e:
            logger.warning(f"Error querying university in lookup: {e}")

    # 2. Truy vấn Phân tích chi tiết 1 ngành cụ thể tại Trường (nếu có cả trường và ngành)
    if (uni_code or uni_name) and major_kws:
        cypher_prog = """
        MATCH (u:University)
        WHERE ($code <> '' AND (toUpper(coalesce(u.short_name, '')) = toUpper($code) OR toUpper(coalesce(u.uni_id, '')) = toUpper($code) OR toUpper(coalesce(u.code, '')) = toUpper($code)))
           OR ($name <> '' AND toLower(u.name) CONTAINS toLower($name))
           OR ($name <> '' AND toLower($name) CONTAINS toLower(u.name))
           OR ($code <> '' AND toLower(u.name) CONTAINS toLower($code))
        WITH u
        ORDER BY CASE 
            WHEN $code <> '' AND toUpper(coalesce(u.short_name, u.code, '')) = toUpper($code) THEN 1
            WHEN $name <> '' AND toLower(u.name) = toLower($name) THEN 2
            ELSE 3 
        END ASC
        LIMIT 1
        MATCH (p:Program)-[:OFFERED_BY]->(u)
        WHERE any(kw IN $keywords WHERE toLower(p.name) CONTAINS toLower(kw))
        OPTIONAL MATCH (p)-[:HAS_FINANCIAL]->(fa:FinancialAspect)
        OPTIONAL MATCH (p)-[:HAS_CRITERIA]->(ad:AdmissionCriteria)
        OPTIONAL MATCH (ad)-[:REQUIRES_GROUP]->(sg:SubjectGroup)
        OPTIONAL MATCH (p)-[:PREPARES_FOR]->(c:Career)
        OPTIONAL MATCH (c)-[:MAPS]->(j:JobPosition)
        WITH u, p, fa, c,
             collect(DISTINCT sg.group_code) AS subject_groups,
             collect(DISTINCT {year: ad.year, score: ad.benchmark_score, method: ad.method}) AS admission_criteria,
             collect(DISTINCT {title: j.title, salary_min: j.salary_min, salary_max: j.salary_max, companies: j.top_hiring_companies})[0..4] AS sample_jobs
        RETURN p.name AS program_name, p.major_code AS major_code, u.name AS university_name,
               fa.tuition_fee_annual AS tuition, subject_groups, admission_criteria,
               c.title AS career_name, c.job_growth_rate AS growth_rate, sample_jobs
        LIMIT 3
        """
        try:
            records_prog = await execute_query_async(cypher_prog, {
                "code": uni_code or "",
                "name": uni_name or "",
                "keywords": major_kws
            })
            if records_prog:
                lookup_data["specific_program_analysis"] = records_prog
        except Exception as e:
            logger.warning(f"Error querying program analysis in lookup: {e}")

    # 3. Truy vấn Ngành nghề & Việc làm CareerViet (nếu hỏi về nghề hoặc ngành)
    career_query_term = major_kws[0] if major_kws else ""
    if career_query_term:
        cypher_career = """
        MATCH (c:Career)
        WHERE toLower(c.title) CONTAINS toLower($career_query)
           OR any(kw IN $keywords WHERE toLower(c.title) CONTAINS toLower(kw) OR toLower(kw) CONTAINS toLower(c.title))
        OPTIONAL MATCH (h:HollandType)-[:MATCH]->(c)
        OPTIONAL MATCH (c)-[:MAPS]->(j:JobPosition)
        OPTIONAL MATCH (p:Program)-[:PREPARES_FOR]->(c)
        OPTIONAL MATCH (p)-[:OFFERED_BY]->(u:University)
        OPTIONAL MATCH (p)-[:HAS_FINANCIAL]->(fa:FinancialAspect)
        WITH c, collect(DISTINCT h.code)[0..3] AS holland_codes,
             collect(DISTINCT {
                 title: j.title,
                 salary_min: j.salary_min,
                 salary_max: j.salary_max,
                 salary_display: j.salary_display,
                 requirements: j.requirements,
                 companies: j.top_hiring_companies
             })[0..6] AS positions,
             collect(DISTINCT {
                 program: p.name,
                 university: coalesce(u.short_name, u.name),
                 tuition: fa.tuition_fee_annual
             })[0..6] AS training_universities
        RETURN c.career_id AS career_id, c.title AS title, c.description AS description,
               c.job_growth_rate AS job_growth_rate, c.top_hiring_companies AS hiring_partners,
               holland_codes, positions, training_universities
        LIMIT 1
        """
        try:
            records_career = await execute_query_async(cypher_career, {
                "career_query": career_query_term,
                "keywords": major_kws
            })
            if records_career:
                lookup_data["career_insight"] = records_career[0]
        except Exception as e:
            logger.warning(f"Error querying career in lookup: {e}")

    # Đóng gói ngữ cảnh cá nhân hóa của học sinh
    student_context = {}
    if student_score:
        student_context["student_score"] = student_score
    if student_group:
        student_context["student_group"] = student_group
    if student_budget:
        student_context["budget_vnd_year"] = student_budget
    if student_city:
        student_context["preferred_city"] = student_city
    if holland_code:
        student_context["holland_code"] = holland_code
    if student_context:
        lookup_data["student_profile"] = student_context

    # 4. LLM Generation: Tổng hợp lời tư vấn sắc sảo, chuyên sâu
    sys_prompt = (
        "Bạn là Chuyên gia Cố vấn Tuyển sinh Đại học & Định hướng Nghề nghiệp AI của hệ thống GraphRAG.\n"
        "Nhiệm vụ của bạn là giải đáp toàn diện, chuyên nghiệp, truyền cảm hứng và trung thực cho học sinh.\n\n"
        "NGUYÊN TẮC TƯ VẤN (CONSULTING PRINCIPLES):\n"
        "1. Dữ liệu thực chứng (Knowledge Graph Grounding): Khi trả lời về học phí, điểm chuẩn, vị trí việc làm, dải lương và doanh nghiệp tuyển dụng, hãy sử dụng chính xác các số liệu từ Knowledge Graph được cung cấp bên dưới (tuyệt đối không bịa đặt số liệu sai lệch).\n"
        "2. ĐÚNG TRƯỜNG, ĐÚNG NGÀNH (STRICT TARGET FOCUS): Luôn trả lời đúng và duy nhất về trường đại học hoặc ngành nghề mà học sinh đề cập trong câu hỏi (ví dụ: học sinh hỏi Trường Đại học Bách khoa - ĐHQG TP.HCM (HCMUT) hay Học viện Công nghệ Bưu chính Viễn thông (PTIT) thì PHẢI tập trung tư vấn chính xác cho trường đó, TUYỆT ĐỐI KHÔNG tự ý đổi sang trường khác như Đại học Bách khoa Hà Nội hay HUST, tuyệt đối không nói 'hệ thống chỉ có dữ liệu HUST'). Nếu dữ liệu chi tiết của trường trong Knowledge Graph có hạn, hãy trả lời về trường đó dựa trên kiến thức chuyên môn chính xác của bạn!\n"
        "3. Nếu học sinh hỏi về 1 ngành cụ thể tại 1 trường cụ thể: Hãy phân tích khả năng trúng tuyển dựa trên mức điểm của học sinh (nếu có trong hồ sơ), dải điểm chuẩn các năm, học phí, môi trường đào tạo và cơ hội việc làm sau khi ra trường.\n"
        "4. Nếu học sinh hỏi về 1 nghề nghiệp: Trình bày rõ tiềm năng tăng trưởng, các vị trí công việc tiêu biểu, dải lương tham chiếu thực tế (từ CareerViet), kỹ năng cần có, và gợi ý các trường đại học đào tạo tốt.\n"
        "5. Nếu học sinh hỏi về 1 trường đại học: Giới thiệu vị thế, xếp hạng, các ngành mũi nhọn/nổi bật, học phí và môi trường học tập (ký túc xá, đời sống sinh viên).\n"
        "6. Với các câu hỏi mở/ngoài dữ liệu cứng (ví dụ: cách ôn thi, quy chế thi, phương thức xét tuyển, so sánh, kỹ năng): Hãy vận dụng kiến thức chuyên sâu về hệ thống giáo dục Việt Nam để tư vấn cặn kẽ, rõ ràng, mang tính định hướng cao.\n"
        "7. Phong cách trình bày: Sử dụng Markdown chuyên nghiệp (tiêu đề ##, gạch đầu dòng, in đậm từ khóa quan trọng, bảng so sánh nếu cần), giọng văn ấm áp, thấu hiểu và khích lệ."
    )

    user_content = (
        f"Dữ liệu tra cứu từ Knowledge Graph & Hồ sơ học sinh:\n"
        f"{json.dumps(lookup_data, ensure_ascii=False, indent=2)}\n\n"
        f"Câu hỏi của học sinh:\n\"{prompt}\""
    )

    reply = await _write_gemini_answer(
        writer,
        [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_content}],
        temperature=0.35, max_tokens=1500,
        prefer_native=state.get("prefer_native", False),
    )
    return {"final_text": reply, "clarification_question": None}


# =========================================================================
# Conditional Routing Logic
# =========================================================================

def route_after_intent(state: AgentState) -> str:
    """Điều hướng sau khi phân loại Intent."""
    intent = state.get("intent", "RECOMMEND")
    if intent in ("RECOMMEND", "COMPARE", "LOOKUP"):
        return "extract_slots"
    elif intent == "CHITCHAT":
        return "chitchat"
    else:
        return "out_of_scope"


def route_after_slots(state: AgentState) -> str:
    """Điều hướng sau khi gộp Slots: Tra cứu / So sánh đi thẳng vào lookup_info."""
    slots = state.get("slots", {})
    intent = state.get("intent", "RECOMMEND")

    # 1. Ý định tra cứu chuyên sâu và so sánh luôn đi vào lookup_info
    if intent in ("LOOKUP", "COMPARE"):
        return "lookup_info"
    if intent == "CHITCHAT":
        return "chitchat"
    if intent == "OUT_OF_SCOPE":
        return "out_of_scope"

    # 2. Đề xuất portfolio (RECOMMEND): Nếu thiếu điểm hoặc khối thi thì hỏi lại
    missing = state.get("missing_slots", [])
    if missing:
        return "ask_clarification"

    return "query_neo4j"


# =========================================================================
# Graph Construction & MemorySaver Checkpointer
# =========================================================================

def create_career_agent_graph():
    """Xây dựng và biên dịch LangGraph StateGraph với MemorySaver checkpointer."""
    workflow = StateGraph(AgentState)

    # Thêm các Node
    workflow.add_node("classify_intent", node_classify_intent)
    workflow.add_node("extract_slots", node_extract_slots)
    workflow.add_node("ask_clarification", node_ask_clarification)
    workflow.add_node("lookup_info", node_lookup_info)
    workflow.add_node("query_neo4j", node_query_neo4j)
    workflow.add_node("rank_portfolio", node_rank_portfolio)
    workflow.add_node("generate_advice", node_generate_advice)
    workflow.add_node("chitchat", node_chitchat)
    workflow.add_node("out_of_scope", node_out_of_scope)

    # Thiết lập Điểm khởi đầu
    workflow.set_entry_point("classify_intent")

    # Conditional Edges từ classify_intent
    workflow.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {
            "extract_slots": "extract_slots",
            "chitchat": "chitchat",
            "out_of_scope": "out_of_scope"
        }
    )

    # Conditional Edges từ extract_slots
    workflow.add_conditional_edges(
        "extract_slots",
        route_after_slots,
        {
            "lookup_info": "lookup_info",
            "ask_clarification": "ask_clarification",
            "query_neo4j": "query_neo4j"
        }
    )

    # Quy trình đề xuất hoàn chỉnh
    workflow.add_edge("query_neo4j", "rank_portfolio")
    workflow.add_edge("rank_portfolio", "generate_advice")

    # Các điểm kết thúc
    workflow.add_edge("lookup_info", END)
    workflow.add_edge("generate_advice", END)
    workflow.add_edge("ask_clarification", END)
    workflow.add_edge("chitchat", END)
    workflow.add_edge("out_of_scope", END)

    # Checkpointer cho bộ nhớ phiên
    checkpointer = MemorySaver()
    compiled_app = workflow.compile(checkpointer=checkpointer)

    return compiled_app


# Singleton instance
career_agent_app = create_career_agent_graph()
