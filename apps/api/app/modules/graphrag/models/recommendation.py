"""
API Request and Response Models for Recommendation Engine and AI Consultation.
Bridges Frontend Web forms, Cypher Hard Constraint Pruning, and Ollama LLM Context.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .enums import AdmissionMethod, Gender


class RecommendationRequest(BaseModel):
    """Payload gửi từ Form tư vấn của học sinh lên Backend FastAPI"""
    target_year: int = Field(2025, ge=2024, le=2030, description="Năm xét tuyển dự kiến")
    student_method: AdmissionMethod = Field(AdmissionMethod.THPT, description="Phương thức xét tuyển")
    student_group_code: str = Field(..., description="Khối thi (VD: 'A00', 'D01')")
    student_score: float = Field(..., ge=0.0, le=1200.0, description="Điểm thi của học sinh (theo thang của phương thức)")
    max_annual_budget: int = Field(..., ge=0, description="Ngân sách học phí tối đa gia đình có thể chi trả/năm (VND)")
    student_gender: Gender = Field(Gender.MALE, description="Giới tính học sinh")
    student_height: Optional[float] = Field(None, ge=100.0, le=250.0, description="Chiều cao học sinh (cm)")
    student_eye_degree: Optional[float] = Field(None, ge=0.0, le=15.0, description="Độ cận thị học sinh (đi-ốp)")
    preferred_city: Optional[str] = Field(None, description="Tỉnh/Thành phố ưu tiên học (Hà Nội, TP.HCM, Đà Nẵng...)")
    holland_code: str = Field(..., min_length=3, max_length=3, description="Mã 3 ký tự Holland RIASEC (VD: 'RIA')")
    bonus_points: Optional[float] = Field(0.0, ge=0.0, description="Tổng điểm cộng/ưu tiên (khu vực + đối tượng) đã quy đổi")


class RecommendationResultItem(BaseModel):
    """Một kết quả ngành/trường phù hợp trích xuất tất định từ Knowledge Graph"""
    university_id: str
    university_name: str
    university_short_name: Optional[str] = None
    faculty_ratio: Optional[float] = None
    facilities: List[str] = Field(default_factory=list)
    program_id: str
    program_name: str
    credential: str
    prerequisites: Optional[str] = None
    accreditation: Optional[str] = None
    benchmark_score: float
    minimum_threshold: Optional[float] = Field(None, description="Điểm sàn / ngưỡng đảm bảo chất lượng đầu vào")
    score_margin: float = Field(..., description="Điểm dôi dư: (student_score + bonus_points) - benchmark_score")
    official_tuition: int
    is_subsidized: bool = Field(False, description="Được nhà nước miễn/trợ cấp học phí")
    actual_tuition: int = Field(..., description="Học phí thực tế sinh viên phải trả")
    career_name: str
    job_growth_rate: float
    hiring_companies: List[str] = Field(default_factory=list)
    holland_match_score: float
    city: str
    transport_score: Optional[int] = None
    safety_level: str = Field("Safe", description="'Safe' nếu margin >= 1.5, 'Target' nếu 0 <= margin < 1.5, 'Reach' nếu sát nút")


class RecommendationResponse(BaseModel):
    """Phản hồi danh sách trường/ngành kèm metadata phân tích"""
    total_found: int
    target_year: int
    holland_code: str
    student_group_code: str
    results: List[RecommendationResultItem] = Field(default_factory=list)


class AIConsultStreamRequest(BaseModel):
    """Yêu cầu sinh báo cáo tư vấn ngôn ngữ tự nhiên từ Local LLM (Ollama)"""
    student_id: Optional[str] = None
    query_text: str = Field(..., description="Câu hỏi hoặc tâm sự của học sinh (VD: 'Em thích IT nhưng sợ toán khó...')")
    recommendation_context: List[RecommendationResultItem] = Field(..., description="Sub-graph kết quả từ Neo4j để LLM bám vào trả lời")


class ChatPromptRequest(BaseModel):
    conversation: List[Dict[str, str]] = Field(default_factory=list)
    prompt: str = Field(..., description="Prompt ngôn ngữ tự nhiên (VD: 'Em thi A00 26 điểm, thích lập trình web ở HCM...')")
    target_year: int = Field(2026, ge=2024, le=2030, description="Năm tuyển sinh mục tiêu")
    stream: bool = Field(False, description="Có stream Server-Sent Events hay không")

    def get_prompt_text(self) -> str:
        return self.prompt


class ExtractedIntent(BaseModel):
    """Kết quả bóc tách từ prompt tự nhiên của học sinh"""
    student_score: Optional[float] = None
    student_group_code: Optional[str] = None
    target_year: int = 2026
    max_annual_budget: Optional[int] = None
    preferred_city: Optional[str] = None
    student_gender: str = "Any"
    student_height: Optional[float] = None
    student_eye_degree: Optional[float] = None
    inferred_holland_code: Optional[str] = "RIA"
    target_career_keywords: List[str] = Field(default_factory=list)
    raw_prompt: str = ""
    profile_context: Dict[str, Any] = Field(default_factory=dict)


class ScoredProgramItem(RecommendationResultItem):
    """Bản ghi chương trình đào tạo kèm điểm số xếp hạng đa tiêu chí (MCDM)"""
    mcdm_score: float = Field(0.0, description="Điểm tổng hợp xếp hạng đa tiêu chí (0.0 -> 1.0)")
    margin_score: float = Field(0.0, description="Điểm an toàn biên độ (Sigmoid)")
    holland_score: float = Field(0.0, description="Điểm khớp tính cách Holland")
    cost_score: float = Field(0.0, description="Điểm tiết kiệm học phí")
    market_score: float = Field(0.0, description="Điểm nhu cầu thị trường & CareerViet")
    semantic_score: float = Field(0.0, description="Điểm khớp từ khóa ngữ nghĩa")
    portfolio_tier: str = Field("Target", description="'Reach' (Mạo hiểm), 'Target' (Vừa sức), 'Safe' (Chắc ăn)")
    top_jobs_market: List[str] = Field(default_factory=list, description="Vị trí việc làm thực tế cào từ CareerViet")


class PortfolioRecommendationResponse(BaseModel):
    """Phản hồi danh mục khuyến nghị phân tầng chiến lược Reach - Target - Safe"""
    extracted_intent: ExtractedIntent
    total_found: int
    reach_programs: List[ScoredProgramItem] = Field(default_factory=list, description="Nguyện vọng mạo hiểm (biên độ -0.5 -> 0.5)")
    target_programs: List[ScoredProgramItem] = Field(default_factory=list, description="Nguyện vọng vừa sức (biên độ 0.5 -> 1.5)")
    safe_programs: List[ScoredProgramItem] = Field(default_factory=list, description="Nguyện vọng an toàn cao (biên độ >= 1.5)")
    all_candidates: List[ScoredProgramItem] = Field(default_factory=list, description="Toàn bộ danh sách ứng viên khớp điểm và bộ lọc đồ thị")
    ai_consultation: Optional[str] = None
