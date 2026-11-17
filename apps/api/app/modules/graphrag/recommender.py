"""
Multi-Criteria Recommendation & Strategic Portfolio Ranking Engine.
Computes MCDM composite scores (Sigmoid Margin, Holland RIASEC, Cost Saving, CareerViet Market Demand)
and allocates candidates into Strategic Admissions Portfolios (Reach, Target, Safe).
"""

import math
from typing import Dict, List, Optional, Tuple
try:
    from .models.recommendation import (
        RecommendationResultItem,
        ScoredProgramItem,
        PortfolioRecommendationResponse,
        ExtractedIntent
    )
except ImportError:
    from models.recommendation import (
        RecommendationResultItem,
        ScoredProgramItem,
        PortfolioRecommendationResponse,
        ExtractedIntent
    )

# Trọng số mặc định của hàm xếp hạng đa tiêu chí (MCDM)
WEIGHTS = {
    "margin": 0.35,    # Độ an toàn điểm số (Sigmoid)
    "holland": 0.25,   # Độ tương thích tính cách nghề nghiệp
    "cost": 0.15,      # Mức độ tiết kiệm chi phí học phí
    "market": 0.15,    # Triển vọng thị trường & dữ liệu việc làm CareerViet
    "semantic": 0.10,  # Độ khớp từ khóa ngành nghề mà học sinh đề cập
}


def compute_sigmoid_margin_score(margin: float, k: float = 0.8) -> float:
    """
    Tính điểm an toàn theo hàm Sigmoid:
    - margin = 0.0 -> score = 0.5
    - margin = +2.0 -> score = 0.83 (rất an toàn)
    - margin = -1.0 -> score = 0.31 (mạo hiểm)
    """
    try:
        return 1.0 / (1.0 + math.exp(-k * margin))
    except OverflowError:
        return 0.0 if margin < 0 else 1.0


def compute_cost_score(actual_tuition: int, max_budget: Optional[int]) -> float:
    """Tính điểm tiết kiệm tài chính"""
    if not max_budget or max_budget <= 0:
        return 0.8
    if actual_tuition > max_budget:
        return 0.1  # Bị phạt nặng nếu vượt ngân sách
    ratio = actual_tuition / max_budget
    return max(0.2, 1.0 - (ratio * 0.6))


def compute_market_score(growth_rate: float, hiring_companies: List[str]) -> float:
    """Tính điểm nhu cầu thị trường từ tăng trưởng ngành và số công ty CareerViet đang tuyển"""
    # Chuẩn hóa tăng trưởng: 15% tăng trưởng tương đương 0.8 điểm
    growth_factor = min(1.0, max(0.0, growth_rate / 20.0))
    # Yếu tố doanh nghiệp tuyển dụng thực tế
    company_factor = 0.8 if hiring_companies and len(hiring_companies) > 0 else 0.4
    return (growth_factor * 0.6) + (company_factor * 0.4)


def compute_semantic_score(program_name: str, career_name: str, keywords: List[str]) -> float:
    """Tính điểm tương đồng ngữ nghĩa từ khóa ngành học"""
    if not keywords:
        return 0.7  # Điểm trung tính nếu người dùng không chỉ định ngành hẹp
    combined = (program_name + " " + career_name).lower()
    matches = sum(1 for kw in keywords if kw.lower() in combined)
    if matches >= 2:
        return 1.0
    elif matches == 1:
        return 0.85
    return 0.3


def rank_and_score_programs(
    raw_candidates: List[RecommendationResultItem],
    intent: ExtractedIntent,
    weights: Optional[Dict[str, float]] = None
) -> List[ScoredProgramItem]:
    """
    Chấm điểm từng chương trình đào tạo theo thuật toán MCDM
    """
    w = weights or WEIGHTS
    scored_list: List[ScoredProgramItem] = []

    for item in raw_candidates:
        s_margin = compute_sigmoid_margin_score(item.score_margin)
        s_holland = min(1.0, max(0.0, item.holland_match_score))
        s_cost = compute_cost_score(item.actual_tuition, intent.max_annual_budget)
        s_market = compute_market_score(item.job_growth_rate, item.hiring_companies)
        s_semantic = compute_semantic_score(item.program_name, item.career_name, intent.target_career_keywords)

        # Tính tổng điểm hợp phần
        mcdm = (
            w["margin"] * s_margin +
            w["holland"] * s_holland +
            w["cost"] * s_cost +
            w["market"] * s_market +
            w["semantic"] * s_semantic
        )

        # Xác định phân tầng danh mục nguyện vọng
        margin = item.score_margin
        if margin < 0.5:
            tier = "Reach"    # Mạo hiểm / Mơ ước (-0.5 -> 0.5)
        elif margin < 2.0:
            tier = "Target"   # Vừa sức / Mục tiêu chính (0.5 -> 2.0)
        else:
            tier = "Safe"     # An toàn / Bảo hiểm (>= 2.0)

        scored_item = ScoredProgramItem(
            **item.model_dump(),
            mcdm_score=round(mcdm, 4),
            margin_score=round(s_margin, 4),
            holland_score=round(s_holland, 4),
            cost_score=round(s_cost, 4),
            market_score=round(s_market, 4),
            semantic_score=round(s_semantic, 4),
            portfolio_tier=tier,
            top_jobs_market=item.hiring_companies[:3]
        )
        scored_list.append(scored_item)

    # Sắp xếp giảm dần theo điểm tổng hợp MCDM
    scored_list.sort(key=lambda x: x.mcdm_score, reverse=True)
    return scored_list


def build_portfolio_recommendations(
    scored_candidates: List[ScoredProgramItem],
    intent: ExtractedIntent,
    max_per_tier: int = 3
) -> PortfolioRecommendationResponse:
    """
    Phân bổ ứng viên vào 3 giỏ chiến lược: Reach, Target, Safe
    """
    reach = [p for p in scored_candidates if p.portfolio_tier == "Reach"][:max_per_tier]
    target = [p for p in scored_candidates if p.portfolio_tier == "Target"][:max_per_tier]
    safe = [p for p in scored_candidates if p.portfolio_tier == "Safe"][:max_per_tier]

    # Nếu một giỏ nào bị trống, cân đối lại từ danh sách tổng
    if not target and scored_candidates:
        target = scored_candidates[:max_per_tier]

    return PortfolioRecommendationResponse(
        extracted_intent=intent,
        total_found=len(scored_candidates),
        reach_programs=reach,
        target_programs=target,
        safe_programs=safe,
        all_candidates=scored_candidates,
        ai_consultation=None
    )
