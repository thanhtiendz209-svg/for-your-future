"""
Assessments Schemas.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SavePersonalityRequest(BaseModel):
    test_type: str = Field(..., description="RIASEC, MBTI, hoặc BIGFIVE")
    result_code: str = Field(..., description="Mã kết quả (VD: 'RIA', 'INTJ')")
    scores_detail: Dict[str, Any] = Field(default_factory=dict)
    top_traits: List[str] = Field(default_factory=list)
    title: Optional[str] = None
    summary: Optional[str] = None


class PersonalityItemResponse(BaseModel):
    result_id: str
    test_type: str
    result_code: str
    scores_detail: Dict[str, Any]
    top_traits: List[str]
    title: Optional[str] = None
    summary: Optional[str] = None
    completed_at: datetime


class SaveCompetencyRequest(BaseModel):
    test_type: str = Field("V-ACT", description="V-ACT, HSA, TSA, INTERNAL")
    quant_score: Optional[float] = None
    verbal_score: Optional[float] = None
    logic_score: Optional[float] = None
    data_analysis_score: Optional[float] = None
    total_score: float
    max_scale: float = 1200.0


class CompetencyResponse(BaseModel):
    assessment_id: str
    test_type: str
    quant_score: Optional[float]
    verbal_score: Optional[float]
    logic_score: Optional[float]
    data_analysis_score: Optional[float]
    total_score: float
    max_scale: float
    percentile: Optional[float]
    completed_at: datetime

