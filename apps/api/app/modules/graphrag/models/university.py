"""
University, Program, and Educational Ontology Models (Pydantic v2).
Aligned with Schema.org (EducationalOccupationalProgram, CollegeOrUniversity) and CTDL.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl
from .enums import UniversityType, DegreeLevel, ProgramLanguage, Region, AdmissionMethod, GenderRequirement, ScholarshipType


class HollandType(BaseModel):
    """Node tri thức tĩnh đại diện cho 1 trong 120 mã RIASEC trong Knowledge Graph"""
    code: str = Field(..., description="Mã 3 ký tự Holland (VD: 'RIA', 'SEC')")
    name: str = Field(..., description="Tên định danh nhóm (VD: 'Kỹ thuật - Nghiên cứu - Nghệ thuật')")
    primary_traits: List[str] = Field(default_factory=list, description="Các nét tính cách chủ đạo")
    description: str = Field(..., description="Mô tả hành vi và sở thích làm việc")


class SubjectGroup(BaseModel):
    """Tổ hợp môn xét tuyển chuẩn quốc gia"""
    group_code: str = Field(..., description="Mã khối thi (A00, A01, B00, C00, D01, D07...)")
    group_name: str = Field(..., description="Tên khối thi (VD: 'Toán, Vật lý, Hóa học')")
    subjects: List[str] = Field(..., description="Danh sách các môn thi trong khối")


class Location(BaseModel):
    """Địa điểm cơ sở trường học và mức độ tiếp cận giao thông"""
    location_id: str = Field(..., description="Mã địa điểm (VD: 'LOC_HCM_Q10')")
    campus_name: str = Field(..., description="Tên cơ sở")
    address: str = Field(..., description="Địa chỉ chi tiết")
    city: str = Field(..., description="Tỉnh / Thành phố chuẩn hóa (Hà Nội, TP.HCM, Đà Nẵng)")
    region: Region = Field(..., description="Miền (North, Central, South)")
    cost_of_living_index: int = Field(70, ge=1, le=100, description="Chỉ số sinh hoạt phí khu vực lân cận")
    public_transport_score: Optional[int] = Field(None, ge=1, le=100, description="Điểm thuận tiện giao thông công cộng (bus/metro)")
    latitude: Optional[float] = Field(None, description="Vĩ độ")
    longitude: Optional[float] = Field(None, description="Kinh độ")


class FinancialAspect(BaseModel):
    """Học phí và chính sách bù giá đào tạo (Edge Case Tuyển sinh Việt Nam)"""
    financial_id: str = Field(..., description="Mã bản ghi tài chính")
    academic_year: int = Field(..., ge=2023, le=2030, description="Năm học áp dụng (bắt buộc dùng trong lọc)")
    tuition_fee_annual: int = Field(..., ge=0, description="Học phí niêm yết hàng năm (VND)")
    tuition_subsidy: bool = Field(False, description="Được nhà nước trợ cấp/miễn phí hay không (ngành Sư phạm NĐ 116)")
    effective_annual_cost: int = Field(..., ge=0, description="Học phí thực tế sinh viên phải trả sau bù giá (dùng để lọc ngân sách)")
    tuition_fee_per_credit: Optional[int] = Field(None, ge=0, description="Học phí 1 tín chỉ")
    other_fees_annual: int = Field(0, ge=0, description="Chi phí khác (BHYT, CSVC, tài liệu)")
    currency: str = Field("VND", description="Đơn vị tiền tệ")
    expected_annual_increase_rate: float = Field(0.1, ge=0.0, le=0.3, description="Biên độ tăng học phí dự kiến/năm")
    tuition_note: Optional[str] = Field(None, description="Ghi chú đóng học phí")


class AdmissionCriteria(BaseModel):
    """Tiêu chí tuyển sinh, điểm chuẩn và điều kiện thể lực định lượng"""
    criteria_id: str = Field(..., description="Mã tiêu chí (VD: 'AD_BKA_IT1_2025_THPT')")
    year: int = Field(..., ge=2023, le=2030, description="Năm tuyển sinh (Bắt buộc lọc)")
    is_latest: bool = Field(True, description="Đánh dấu điểm chuẩn mới nhất")
    method: AdmissionMethod = Field(AdmissionMethod.THPT, description="Phương thức xét tuyển")
    benchmark_score: float = Field(..., ge=0.0, description="Điểm chuẩn trúng tuyển")
    score_scale: float = Field(30.0, ge=1.0, description="Thang điểm tối đa (30, 40, 100, 1200)")
    quota: Optional[int] = Field(None, ge=1, description="Chỉ tiêu tuyển sinh của ngành")
    gender_requirement: GenderRequirement = Field(GenderRequirement.ANY, description="Ràng buộc giới tính (Any, Male, Female)")
    min_height_male: Optional[float] = Field(None, ge=120.0, le=220.0, description="Chiều cao tối thiểu cho nam (cm)")
    min_height_female: Optional[float] = Field(None, ge=120.0, le=220.0, description="Chiều cao tối thiểu cho nữ (cm)")
    max_eye_degree: Optional[float] = Field(None, ge=0.0, le=15.0, description="Độ cận tối đa cho phép (đi-ốp)")
    require_health_certificate: bool = Field(False, description="Yêu cầu giấy khám sức khỏe chuyên ngành")
    minimum_threshold: Optional[float] = Field(None, ge=0.0, description="Điểm sàn / ngưỡng đảm bảo chất lượng đầu vào để được xét tuyển")
    tie_breaker_subject: Optional[str] = Field(None, description="Môn ưu tiên xét tuyển khi hòa điểm (VD: 'Toán')")
    tie_breaker_min_score: Optional[float] = Field(None, ge=0.0, description="Điểm tối thiểu môn ưu tiên khi hòa điểm")
    tie_breaker_order: Optional[int] = Field(None, ge=1, description="Thứ tự nguyện vọng tối đa được ưu tiên khi hòa điểm (VD: NV <= 2)")
    priority_policy: Optional[str] = Field(None, description="Chính sách ưu tiên tuyển sinh")
    special_conditions: Optional[str] = Field(None, description="Tiêu chí phụ khi hòa điểm")


class Scholarship(BaseModel):
    """Chính sách học bổng dành cho sinh viên"""
    scholarship_id: str = Field(..., description="Mã học bổng")
    name: str = Field(..., description="Tên học bổng")
    type: ScholarshipType = Field(ScholarshipType.MERIT, description="Loại học bổng")
    amount_annual: Optional[int] = Field(None, ge=0, description="Trị giá tiền mặt (VND)")
    coverage_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Tỷ lệ miễn giảm học phí (%)")
    conditions_summary: str = Field(..., description="Tiêu chí điều kiện xét nhận")
    min_gpa_required: Optional[float] = Field(None, ge=0.0, le=10.0, description="GPA tối thiểu yêu cầu")
    total_slots: Optional[int] = Field(None, ge=1, description="Số suất học bổng có sẵn")


class ProgramType(BaseModel):
    """Phân loại hình thức chương trình đào tạo"""
    type_id: str = Field(..., description="Mã loại hình (PT_STANDARD, PT_HONORS, PT_ADVANCED, PT_INTERNATIONAL)")
    type_name: str = Field(..., description="Tên loại hình (Chương trình Chuẩn, CLC, Tiên tiến...)")
    description: Optional[str] = Field(None, description="Mô tả loại hình")


class Program(BaseModel):
    """Ngành / Chương trình đào tạo cụ thể (Chuẩn Schema.org EducationalOccupationalProgram)"""
    program_id: str = Field(..., description="Mã chương trình (VD: 'BKA_IT1')")
    name: str = Field(..., description="Tên ngành đào tạo")
    major_code: str = Field(..., description="Mã ngành quốc gia chuẩn Bộ GD&ĐT (VD: '7480201')")
    degree_level: DegreeLevel = Field(DegreeLevel.ENGINEER, description="Bằng cấp tốt nghiệp")
    educational_credential_awarded: str = Field(..., description="Văn bằng cụ thể khi tốt nghiệp (Schema.org)")
    program_prerequisites: Optional[str] = Field(None, description="Điều kiện tiên quyết đầu vào (IELTS, Toán nâng cao)")
    accreditation: Optional[str] = Field(None, description="Kiểm định chất lượng (ABET, AUN-QA)")
    application_deadline: Optional[str] = Field(None, description="Hạn nộp hồ sơ đợt chính (YYYY-MM-DD)")
    duration_years: float = Field(4.0, ge=1.0, le=7.0, description="Thời gian đào tạo (năm)")
    language: ProgramLanguage = Field(ProgramLanguage.VIETNAMESE, description="Ngôn ngữ giảng dạy")
    total_credits: Optional[int] = Field(None, ge=60, description="Tổng số tín chỉ")
    curriculum_url: Optional[str] = Field(None, description="Link khung chương trình chi tiết")
    description: Optional[str] = Field(None, description="Tóm tắt giới thiệu ngành")


class University(BaseModel):
    """Trường Đại học / Học viện (Chuẩn Schema.org CollegeOrUniversity)"""
    uni_id: str = Field(..., description="Mã trường chuẩn Bộ GD&ĐT (VD: 'BKA', 'QSK', 'FTU')")
    name: str = Field(..., description="Tên trường đầy đủ")
    type: UniversityType = Field(UniversityType.PUBLIC, description="Loại hình trường (Công lập, Tư thục, Quốc tế)")
    ranking_national: Optional[int] = Field(None, ge=1, description="Thứ hạng trong nước")
    ranking_global: Optional[int] = Field(None, ge=1, description="Thứ hạng quốc tế (QS/THE)")
    student_faculty_ratio: Optional[float] = Field(None, ge=1.0, description="Tỷ lệ sinh viên/giảng viên (QS/THE)")
    international_student_ratio: Optional[float] = Field(None, ge=0.0, le=100.0, description="Tỷ lệ sinh viên quốc tế (%)")
    campus_facilities: List[str] = Field(default_factory=list, description="Danh mục cơ sở vật chất")
    website: str = Field(..., description="Trang chủ chính thức")
    admissions_url: str = Field(..., description="Cổng thông tin tuyển sinh")
    logo_url: Optional[str] = Field(None, description="Link ảnh logo trường")
    founded_year: Optional[int] = Field(None, ge=1900, description="Năm thành lập")
    has_dormitory: bool = Field(True, description="Có ký túc xá cho sinh viên")
