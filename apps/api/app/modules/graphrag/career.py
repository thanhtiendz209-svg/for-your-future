"""
Career and Industry Domain Knowledge Graph Models (Pydantic v2).
Represents static domain entities in Neo4j and API serialization.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from .enums import GrowthOutlook, WorkEnvironment, SkillCategory, ExperienceLevel, JobType, CertRecognitionLevel


class CompetencyRequirement(BaseModel):
    """Yêu cầu năng lực tư duy cốt lõi đối với ngành nghề"""
    req_id: str = Field(..., description="Mã định danh yêu cầu")
    competency_name: str = Field(..., description="Tên năng lực (Logic, Quantitative, Verbal, Spatial)")
    required_level: int = Field(..., ge=1, le=5, description="Cấp độ tối thiểu cần có (1-5)")
    min_score_percentile: float = Field(..., ge=0.0, le=100.0, description="Điểm bách phân vị tối thiểu")
    weight: float = Field(..., ge=0.0, le=1.0, description="Trọng số đối với ngành nghề")


class Skill(BaseModel):
    """Kỹ năng chuyên môn cứng và kỹ năng mềm"""
    skill_id: str = Field(..., description="Mã kỹ năng chuẩn (VD: 'SKILL_PYTHON')")
    name: str = Field(..., description="Tên kỹ năng")
    category: SkillCategory = Field(SkillCategory.HARD, description="Phân loại kỹ năng")
    description: Optional[str] = Field(None, description="Mô tả kỹ năng")
    proficiency_scale: int = Field(5, description="Thang đánh giá thành thạo")


class JobPosition(BaseModel):
    """Vị trí công việc cụ thể trên thị trường lao động"""
    position_id: str = Field(..., description="Mã vị trí công việc")
    title: str = Field(..., description="Tên chức danh công việc")
    experience_level: ExperienceLevel = Field(ExperienceLevel.JUNIOR, description="Cấp bậc kinh nghiệm")
    experience_years_min: int = Field(0, ge=0, description="Số năm kinh nghiệm tối thiểu")
    salary_min: int = Field(..., ge=0, description="Mức lương tối thiểu (VND)")
    salary_max: int = Field(..., ge=0, description="Mức lương tối đa (VND)")
    job_type: JobType = Field(JobType.FULL_TIME, description="Hình thức làm việc")


class ProfessionalCert(BaseModel):
    """Chứng chỉ chuyên môn nghề nghiệp quốc tế và quốc gia"""
    cert_id: str = Field(..., description="Mã chứng chỉ")
    name: str = Field(..., description="Tên chứng chỉ")
    provider: str = Field(..., description="Tổ chức cấp chứng chỉ")
    validity_years: Optional[int] = Field(None, description="Thời hạn chứng chỉ (năm)")
    estimated_cost_usd: Optional[float] = Field(None, description="Chi phí thi (USD)")
    recognition_level: CertRecognitionLevel = Field(CertRecognitionLevel.GLOBAL, description="Mức độ công nhận")


class Career(BaseModel):
    """Ngành nghề cốt lõi - Trung tâm định hướng Knowledge Graph"""
    career_id: str = Field(..., description="Mã nghề chuẩn (VD: 'CAR_DATA_SCIENTIST')")
    title: str = Field(..., description="Tên nghề nghiệp tiếng Việt")
    domain: str = Field(..., description="Lĩnh vực chính (CNTT, Y tế, Tài chính...)")
    description: str = Field(..., description="Mô tả công việc và sứ mệnh")
    growth_outlook: GrowthOutlook = Field(GrowthOutlook.HIGH, description="Đánh giá định tính triển vọng")
    job_growth_rate: float = Field(..., description="Tỷ lệ tăng trưởng việc làm hàng năm (% cụ thể, VD 0.15 = 15%/năm)")
    top_hiring_companies: List[str] = Field(default_factory=list, description="Top doanh nghiệp/tập đoàn tuyển dụng nhiều nhất")
    avg_salary_entry: float = Field(..., ge=0.0, description="Mức lương khởi điểm ước tính (Triệu VND/tháng)")
    avg_salary_mid: float = Field(..., ge=0.0, description="Mức lương sau 3-5 năm kinh nghiệm (Triệu VND/tháng)")
    work_environment: WorkEnvironment = Field(WorkEnvironment.OFFICE, description="Môi trường làm việc chính")


class Industry(BaseModel):
    """Ngành công nghiệp / Lĩnh vực sản xuất kinh doanh"""
    industry_id: str = Field(..., description="Mã ngành kinh tế")
    name: str = Field(..., description="Tên ngành công nghiệp")
    sector: str = Field(..., description="Nhóm ngành kinh tế vĩ mô")
    market_size_usd: Optional[float] = Field(None, description="Quy mô thị trường (tỷ USD)")
    key_enterprises: List[str] = Field(default_factory=list, description="Doanh nghiệp tiêu biểu trong ngành")


class MarketTrend(BaseModel):
    """Xu hướng công nghệ & thị trường lao động tương lai"""
    trend_id: str = Field(..., description="Mã xu hướng")
    name: str = Field(..., description="Tên xu hướng (AI, ESG, Bán dẫn...)")
    sector: str = Field(..., description="Lĩnh vực tác động")
    growth_rate_annual: float = Field(..., description="Tỷ lệ tăng trưởng dự phóng hàng năm")
    impact_level: str = Field("High", description="Mức độ tác động (Critical, High, Moderate)")
    forecast_year: int = Field(2030, description="Mốc năm dự phóng")
    source_report: Optional[str] = Field(None, description="Báo cáo tham chiếu")
