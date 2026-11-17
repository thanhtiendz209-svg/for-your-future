"""
Recommendation Schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    target_year: int = Field(2026, ge=2024, le=2030, description="Năm xét tuyển dự kiến")
    student_method: str = Field("Điểm thi THPT", description="Phương thức xét tuyển (Điểm thi THPT, ĐGNL, Học bạ, Kết hợp)")
    student_group_code: str = Field(..., description="Tổ hợp môn (A00, A01, D01, B00...)")
    student_score: float = Field(..., ge=0.0, le=1200.0, description="Điểm thi của học sinh")
    max_annual_budget: int = Field(..., ge=0, description="Ngân sách học phí tối đa/năm (VND)")
    student_gender: str = Field("Male", description="Male, Female, hoặc Other")
    student_height: Optional[float] = Field(None, ge=100.0, le=250.0, description="Chiều cao (cm)")
    student_eye_degree: Optional[float] = Field(None, ge=0.0, le=20.0, description="Độ cận thị (đi-ốp)")
    preferred_city: Optional[str] = Field(None, description="Thành phố ưu tiên (Hà Nội, TP.HCM, Đà Nẵng...)")
    holland_code: str = Field(..., min_length=3, max_length=3, description="Mã 3 ký tự Holland RIASEC (VD: 'RIA')")
    bonus_points: Optional[float] = Field(0.0, ge=0.0, description="Điểm ưu tiên khu vực + đối tượng đã tính")


class RecommendationResultItem(BaseModel):
    university_id: str
    university_name: str
    university_short_name: Optional[str] = None
    faculty_ratio: Optional[float] = None
    facilities: List[str] = []
    program_id: str
    program_name: str
    credential: str = "Cử nhân"
    benchmark_score: float
    minimum_threshold: Optional[float] = None
    group_code: Optional[str] = None
    tie_breaker_subject: Optional[str] = None
    source_url: Optional[str] = None
    score_margin: float
    official_tuition: int
    is_subsidized: bool = False
    actual_tuition: int
    career_name: str
    job_growth_rate: float
    hiring_companies: List[str] = []
    holland_match_score: float = 1.0
    city: str
    transport_score: Optional[int] = None
    safety_level: str  # Safe, Target, Reach
    warning: Optional[str] = None


class RecommendationResponse(BaseModel):
    total_found: int
    target_year: int
    holland_code: str
    student_group_code: str
    results: List[RecommendationResultItem] = []
    empty_suggestions: Optional[List[str]] = None

