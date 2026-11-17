"""
Student Domain and Transactional Assessment Data Models (Pydantic v2).
Used for client profile state, API request payloads, and relational persistence.
"""

from datetime import date, datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from .enums import (
    Gender,
    PriorityZone,
    AcademicRank,
    IncomeLevel,
    RegionType,
    TestType,
    StandardizedTestType,
    VerificationStatus,
    AdmissionMethod,
)


class StudentProfile(BaseModel):
    """Hồ sơ định danh cá nhân của học sinh THPT (Client Profile / PostgreSQL)"""
    student_id: str = Field(..., description="UUID định danh ẩn danh của học sinh")
    first_name: str = Field(..., description="Tên học sinh")
    last_name: str = Field(..., description="Họ học sinh")
    dob: Optional[date] = Field(None, description="Ngày sinh YYYY-MM-DD")
    gender: Gender = Field(..., description="Giới tính học sinh (Male, Female, Other)")
    email: str = Field(..., description="Email tài khoản")
    phone: Optional[str] = Field(None, description="Số điện thoại liên lạc")
    current_school: Optional[str] = Field(None, description="Trường THPT đang theo học")
    grade_level: int = Field(..., ge=10, le=12, description="Khối lớp (10, 11, 12)")
    target_year: int = Field(..., ge=2024, le=2030, description="Năm thi đại học dự kiến")
    hashed_password: Optional[str] = Field(None, description="Mật khẩu tài khoản đã mã hóa (nếu có)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class HealthProfile(BaseModel):
    """Hồ sơ thể lực và sức khỏe học sinh (Quân đội, Công an, Hàng không, Thể thao)"""
    health_id: str = Field(..., description="UUID định danh hồ sơ sức khỏe")
    student_id: str = Field(..., description="UUID học sinh liên kết")
    height_cm: float = Field(..., ge=100.0, le=250.0, description="Chiều cao học sinh (cm)")
    weight_kg: Optional[float] = Field(None, ge=30.0, le=200.0, description="Cân nặng học sinh (kg)")
    bmi: Optional[float] = Field(None, ge=10.0, le=50.0, description="Chỉ số khối cơ thể (BMI)")
    eye_degree_left: Optional[float] = Field(None, ge=0.0, le=20.0, description="Độ cận thị mắt trái (đi-ốp)")
    eye_degree_right: Optional[float] = Field(None, ge=0.0, le=20.0, description="Độ cận thị mắt phải (đi-ốp)")
    max_eye_degree: Optional[float] = Field(None, ge=0.0, le=20.0, description="Độ cận thị mắt cao hơn (phục vụ lọc tuyển sinh)")
    color_blindness: bool = Field(False, description="Có bị mù màu hay không")
    hearing_status: str = Field("Normal", description="Thính lực (Normal, Impaired)")
    physical_grade: Optional[str] = Field(None, description="Phân loại sức khỏe (Loại 1, Loại 2, Loại 3...)")
    has_health_certificate: bool = Field(False, description="Đã có giấy khám sức khỏe đạt tiêu chuẩn sơ tuyển")
    examined_at: Optional[date] = Field(None, description="Ngày khám sức khỏe gần nhất")


class StudentBackground(BaseModel):
    """Bối cảnh gia đình và ràng buộc tài chính (Hard Constraint Pruning Source)"""
    background_id: str = Field(..., description="UUID bối cảnh gia đình")
    student_id: str = Field(..., description="UUID học sinh liên kết")
    income_level: IncomeLevel = Field(..., description="Mức thu nhập chung")
    exact_income_monthly: Optional[int] = Field(None, ge=0, description="Thu nhập hàng tháng (VND)")
    max_annual_tuition: int = Field(..., ge=0, description="Học phí tối đa 1 năm có thể chi trả (VND) - Điểm chốt lọc Pruning")
    currency: str = Field("VND", description="Đơn vị tiền tệ")
    family_size: Optional[int] = Field(None, ge=1, description="Số thành viên trong gia đình")
    region_type: RegionType = Field(RegionType.URBAN, description="Khu vực sinh sống")
    priority_zone: PriorityZone = Field(PriorityZone.KV3, description="Khu vực ưu tiên tuyển sinh (KV1, KV2-NT, KV2, KV3)")
    priority_object: Optional[str] = Field(None, description="Đối tượng ưu tiên (01, 02, 03... theo quy chế Bộ GD&ĐT)")
    priority_points_raw: Optional[float] = Field(None, ge=0.0, description="Điểm ưu tiên thô theo khu vực/đối tượng")
    priority_points_calculated: Optional[float] = Field(None, ge=0.0, description="Điểm ưu tiên thực tế sau khi tính quy chế giảm dần")
    financial_hardship: bool = Field(False, description="Thuộc diện hộ nghèo / gia đình chính sách")

class SubjectScore(BaseModel):
    """Điểm chi tiết của một môn học"""
    subject_name: str = Field(..., description="Tên môn: Toán, Vật lý, Hóa học, Tiếng Anh...")
    score_grade_10: Optional[float] = Field(None, ge=0, le=10, description="Điểm TB môn lớp 10")
    score_grade_11: Optional[float] = Field(None, ge=0, le=10, description="Điểm TB môn lớp 11")
    score_grade_12: Optional[float] = Field(None, ge=0, le=10, description="Điểm TB môn lớp 12 (hoặc HK1)")
    average_score: Optional[float] = Field(None, ge=0, le=10, description="Điểm TB môn tích lũy (3 năm hoặc 5 HK)")

class ExamScore(BaseModel):
    """Điểm thi tốt nghiệp THPT (nếu có)"""
    subject_name: str = Field(..., description="Tên môn thi")
    score: float = Field(..., ge=0, le=10, description="Điểm thi")

class InternationalCertificate(BaseModel):
    """Chứng chỉ quốc tế & ngoại ngữ (SAT, ACT, A-Level, AP, IB, IELTS, TOEFL, VSTEP, HSK...)"""
    cert_id: str = Field(..., description="UUID chứng chỉ")
    student_id: str = Field(..., description="UUID học sinh liên kết")
    cert_type: str = Field(..., description="Loại chứng chỉ (SAT, ACT, A-Level, AP, IB, IELTS, VSTEP, HSK...)")
    score: float = Field(..., ge=0.0, description="Điểm số đạt được")
    max_score: float = Field(..., ge=0.0, description="Thang điểm tối đa của chứng chỉ")
    issue_date: Optional[date] = Field(None, description="Ngày cấp chứng chỉ")

    verification_status: VerificationStatus = Field(VerificationStatus.PENDING, description="Trạng thái xác thực (Pending, Verified, Rejected)")


class AcademicProfile(BaseModel):
    """Hồ sơ học thuật, điểm học bạ và các chứng chỉ chuẩn hóa"""
    profile_id: str = Field(..., description="UUID hồ sơ học thuật")
    student_id: str = Field(..., description="UUID học sinh liên kết")
    
    # --- GPA theo năm ---
    gpa_grade_10: Optional[float] = Field(None, ge=0.0, le=10.0)
    gpa_grade_11: Optional[float] = Field(None, ge=0.0, le=10.0)
    gpa_grade_12: float = Field(..., ge=0.0, le=10.0)
    gpa_overall: float = Field(..., ge=0.0, le=10.0, description="GPA tích lũy cả cấp 3 (6 học kỳ)")

    gpa_5_semesters: Optional[float] = Field(None, ge=0.0, le=10.0, 
        description="GPA 5 học kỳ (HK1, HK2 lớp 10, 11 và HK1 lớp 12)")
    academic_rank: AcademicRank = Field(AcademicRank.GOOD)

    subject_scores: List[SubjectScore] = Field(default_factory=list, 
        description="Danh sách điểm chi tiết từng môn học")
    exam_scores: List[ExamScore] = Field(default_factory=list, 
        description="Điểm thi tốt nghiệp THPT các môn")
    
    # --- Hạnh kiểm từng năm (phục vụ lọc điều kiện học bạ) ---
    conduct_grade_10: Optional[str] = Field(None, description="Hạnh kiểm lớp 10 (Tốt, Khá, Trung bình, Yếu)")
    conduct_grade_11: Optional[str] = Field(None, description="Hạnh kiểm lớp 11 (Tốt, Khá, Trung bình, Yếu)")
    conduct_grade_12: Optional[str] = Field(None, description="Hạnh kiểm lớp 12 (Tốt, Khá, Trung bình, Yếu)")

    # --- Chứng chỉ chuẩn hóa & Ngoại ngữ đa dạng ---
    ielts_score: Optional[float] = Field(None, ge=0.0, le=9.0)
    sat_score: Optional[int] = Field(None, ge=400, le=1600)
    dgnl_hcm_score: Optional[int] = Field(None, ge=0, le=1200)
    dgnl_hn_score: Optional[int] = Field(None, ge=0, le=150)
    tsa_hust_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    certificates: List[InternationalCertificate] = Field(default_factory=list,
        description="Danh sách chứng chỉ quốc tế và ngoại ngữ (A-Level, AP, IB, VSTEP, HSK...)")


class CompetencyAssessment(BaseModel):
    """Kết quả bài kiểm tra đánh giá năng lực tư duy chuẩn hóa (V-ACT, HSA, TSA, Internal)"""
    assessment_id: str = Field(..., description="UUID bài đánh giá")
    student_id: str = Field(..., description="UUID học sinh")
    test_type: StandardizedTestType = Field(StandardizedTestType.V_ACT, description="Loại kỳ thi chuẩn hóa (V-ACT, HSA, TSA, Internal)")
    test_date: date = Field(default_factory=date.today)
    quant_score: float = Field(..., ge=0.0, description="Điểm tư duy định lượng / Toán (theo thang điểm gốc bài thi)")
    verbal_score: float = Field(..., ge=0.0, description="Điểm tư duy ngôn ngữ / Đọc hiểu (theo thang điểm gốc bài thi)")
    logic_score: Optional[float] = Field(None, ge=0.0, description="Điểm tư duy logic / khoa học (None nếu thi HSA vì HSA không có phần thi riêng)")
    data_analysis_score: Optional[float] = Field(None, ge=0.0, description="Điểm phân tích số liệu (nếu bài thi bóc tách riêng)")
    total_score: float = Field(..., ge=0.0, description="Tổng điểm bài thi thực tế (V-ACT: 1200, HSA: 150, TSA: 100)")
    max_scale: float = Field(1200.0, ge=1.0, description="Thang điểm tối đa của kỳ thi")
    percentile: Optional[float] = Field(None, ge=0.0, le=100.0, description="Phân vị học sinh (nếu có)")


class PersonalityTestResult(BaseModel):
    """Kết quả trắc nghiệm tính cách giao dịch (Lưu trên Client / PostgreSQL)"""
    result_id: str = Field(..., description="UUID kết quả")
    student_id: str = Field(..., description="UUID học sinh")
    test_type: TestType = Field(TestType.RIASEC, description="Loại trắc nghiệm")
    result_code: str = Field(..., min_length=3, max_length=4, description="Mã chữ ký nghề nghiệp (VD: 'RIA' cho Holland, 'INTJ' cho MBTI)")
    scores_detail: Dict[str, float] = Field(default_factory=dict, description="Chi tiết điểm trọn vẹn của cả 6 nhóm R, I, A, S, E, C")
    top_traits: List[str] = Field(default_factory=list, description="Top đặc tính nổi trội hiển thị UI")
    title: str = Field(..., description="Tên định danh nhóm")
    summary: str = Field(..., description="Tóm tắt xu hướng")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Độ tin cậy bài test")
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class Achievement(BaseModel):
    """Thành tích & Giải thưởng học sinh"""
    achievement_id: str = Field(..., description="UUID thành tích")
    student_id: str = Field(..., description="UUID học sinh")
    name: str = Field(..., description="Tên giải thưởng / thành tích")
    category: str = Field("Academic", description="Lĩnh vực (Academic, Science_Tech, Sports, Arts)")
    level: str = Field("National", description="Cấp độ (School, District, Provincial, National, International)")
    rank: str = Field("First", description="Giải thưởng (First, Second, Third, Consolation)")
    year: int = Field(..., description="Năm đạt giải")
    issuing_org: str = Field(..., description="Đơn vị trao giải")
    verification_status: VerificationStatus = Field(VerificationStatus.PENDING, description="Trạng thái xác thực (Pending, Verified, Rejected)")
