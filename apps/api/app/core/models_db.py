"""
SQLAlchemy ORM Models for Relational Data Persistence.
Mapped directly to the Domain Schema (Student, Assessment, Study Ability, Career, University, Market).
Supports PostgreSQL and SQLite.
"""

from datetime import datetime
import uuid
from typing import Any
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Date,
    Text,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ==========================================
# 1. USER & AUTH DOMAIN
# ==========================================
class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="student", nullable=False)  # student, admin
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


# ==========================================
# 2. STUDENT & STUDY ABILITY DOMAIN
# ==========================================
class StudentProfile(Base):
    __tablename__ = "student_profiles"

    student_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=True)
    gender = Column(String(20), default="Other", nullable=False)
    phone = Column(String(20), nullable=True)
    current_school = Column(String(255), nullable=True)
    grade_level = Column(Integer, default=12, nullable=False)
    target_year = Column(Integer, default=2026, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="student_profile")
    background = relationship("StudentBackground", back_populates="student", uselist=False, cascade="all, delete-orphan")
    academic_profile = relationship("AcademicProfile", back_populates="student", uselist=False, cascade="all, delete-orphan")
    health_profile = relationship("HealthProfile", back_populates="student", uselist=False, cascade="all, delete-orphan")
    personality_results = relationship("PersonalityResult", back_populates="student", cascade="all, delete-orphan")
    competency_assessments = relationship("CompetencyAssessment", back_populates="student", cascade="all, delete-orphan")
    recommendation_runs = relationship("RecommendationRun", back_populates="student", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="student", cascade="all, delete-orphan")


class StudentBackground(Base):
    __tablename__ = "student_backgrounds"

    background_id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False, index=True)
    hometown_province = Column(String(100), nullable=True)  # Tỉnh / Thành phố quê quán
    income_level = Column(String(50), default="Medium", nullable=False)
    max_annual_tuition = Column(Integer, default=30000000, nullable=False)  # in VND
    priority_zone = Column(String(20), default="KV3", nullable=False)  # KV1, KV2-NT, KV2, KV3
    priority_object = Column(String(20), default="None", nullable=False)  # 01, 02, 03...
    priority_points_calculated = Column(Float, default=0.0, nullable=False)
    financial_hardship = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("StudentProfile", back_populates="background")


class AcademicProfile(Base):
    __tablename__ = "academic_profiles"

    profile_id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False, index=True)
    gpa_grade_10 = Column(Float, nullable=True)
    gpa_grade_11 = Column(Float, nullable=True)
    gpa_grade_12 = Column(Float, nullable=True)
    gpa_overall = Column(Float, nullable=True)
    gpa_5_semesters = Column(Float, nullable=True)
    academic_rank = Column(String(50), nullable=True)
    conduct_grade_10 = Column(String(50), nullable=True)
    conduct_grade_11 = Column(String(50), nullable=True)
    conduct_grade_12 = Column(String(50), nullable=True)
    ielts_score = Column(Float, nullable=True)
    sat_score = Column(Integer, nullable=True)
    dgnl_hcm_score = Column(Integer, nullable=True)  # ĐHQG TP.HCM thang 1200
    dgnl_hn_score = Column(Integer, nullable=True)   # ĐHQG Hà Nội thang 150
    tsa_hust_score = Column(Float, nullable=True)    # ĐH Bách khoa HN thang 100
    subject_scores = Column(JSON, default=dict)  # {"Math": 8.5, "Physics": 9.0, ...}
    exam_scores = Column(JSON, default=dict)     # {"A00": 26.5, "D01": 24.0, ...}
    certificates = Column(JSON, default=list)    # [{"name": "IELTS", "score": 7.0}]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student = relationship("StudentProfile", back_populates="academic_profile")


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    health_id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False, index=True)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    eye_degree_left = Column(Float, nullable=True)
    eye_degree_right = Column(Float, nullable=True)
    max_eye_degree = Column(Float, nullable=True)
    color_blindness = Column(Boolean, default=False, nullable=False)
    hearing_status = Column(String(50), default="Normal", nullable=False)
    physical_grade = Column(String(50), nullable=True)
    has_health_certificate = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("StudentProfile", back_populates="health_profile")


# ==========================================
# 3. ASSESSMENT DOMAIN
# ==========================================
class PersonalityResult(Base):
    __tablename__ = "personality_results"

    result_id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False, index=True)
    test_type = Column(String(50), nullable=False)  # RIASEC, MBTI, BIGFIVE
    result_code = Column(String(20), nullable=False)  # e.g., "RIA", "INTJ", "OCEAN"
    scores_detail = Column(JSON, default=dict, nullable=False)  # {"R": 24, "I": 28, ...}
    top_traits = Column(JSON, default=list)
    title = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("StudentProfile", back_populates="personality_results")


class CompetencyAssessment(Base):
    __tablename__ = "competency_assessments"

    assessment_id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False, index=True)
    test_type = Column(String(50), nullable=False)  # V-ACT, HSA, TSA, INTERNAL
    quant_score = Column(Float, nullable=True)
    verbal_score = Column(Float, nullable=True)
    logic_score = Column(Float, nullable=True)
    data_analysis_score = Column(Float, nullable=True)
    total_score = Column(Float, nullable=False)
    max_scale = Column(Float, default=1200.0, nullable=False)
    percentile = Column(Float, nullable=True)
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("StudentProfile", back_populates="competency_assessments")


# ==========================================
# 4. UNIVERSITY, PROGRAM & ADMISSIONS DOMAIN
# ==========================================
class University(Base):
    __tablename__ = "universities"

    uni_id = Column(String(50), primary_key=True)  # e.g., "uni-001"
    name = Column(String(255), nullable=False, index=True)
    short_name = Column(String(50), nullable=True, index=True)
    code = Column(String(50), nullable=True)
    type = Column(String(50), default="Public")  # Public, Private, International
    location = Column(String(100), nullable=False)  # Hà Nội, TP.HCM...
    region = Column(String(50), nullable=False)    # Miền Bắc, Miền Trung, Miền Nam
    ranking_national = Column(Integer, nullable=True)
    website = Column(String(255), nullable=True)
    admissions_url = Column(String(255), nullable=True)
    has_dormitory = Column(Boolean, default=False)
    logo = Column(String(255), nullable=True)
    focus_riasec = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    programs = relationship("Program", back_populates="university", cascade="all, delete-orphan")


class Program(Base):
    __tablename__ = "programs"

    program_id = Column(String(100), primary_key=True)  # e.g., "uni-001-IT1"
    uni_id = Column(String(50), ForeignKey("universities.uni_id", ondelete="CASCADE"), nullable=False, index=True)
    major_code = Column(String(50), nullable=False, index=True)  # e.g., "7480201"
    name = Column(String(255), nullable=False, index=True)
    degree_level = Column(String(50), default="Bachelor")
    duration_years = Column(Float, default=4.0)
    tuition_annual = Column(Integer, default=0)
    effective_cost = Column(Integer, default=0)
    is_subsidized = Column(Boolean, default=False)
    faculty_ratio = Column(Float, nullable=True)
    facilities = Column(JSON, default=list)
    career_id = Column(String(50), ForeignKey("careers.career_id", ondelete="SET NULL"), nullable=True)

    university = relationship("University", back_populates="programs")
    career = relationship("Career", back_populates="programs")
    criteria = relationship("AdmissionCriteria", back_populates="program", cascade="all, delete-orphan")


class AdmissionCriteria(Base):
    __tablename__ = "admission_criteria"

    criteria_id = Column(String(100), primary_key=True)
    program_id = Column(String(100), ForeignKey("programs.program_id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, default=2026, nullable=False, index=True)
    method = Column(String(100), nullable=False)  # Thi THPT, ĐGNL...
    group_code = Column(String(20), nullable=True, index=True)  # A00, D01, or None for general
    benchmark_score = Column(Float, nullable=True)
    minimum_threshold = Column(Float, nullable=True)  # Điểm sàn
    score_scale = Column(Float, default=30.0, nullable=False)
    quota = Column(Integer, nullable=True)
    min_height_male = Column(Float, nullable=True)
    min_height_female = Column(Float, nullable=True)
    max_eye_degree = Column(Float, nullable=True)
    gender_requirement = Column(String(20), default="Any")
    tie_breaker_subject = Column(String(50), nullable=True)  # Môn tiêu chí phụ khi hòa điểm (VD: Toán)
    tie_breaker_min_score = Column(Float, nullable=True)     # Điểm tối thiểu môn tiêu chí phụ
    special_conditions = Column(Text, nullable=True)         # Điều kiện bổ sung / tiêu chí phụ
    source_url = Column(String(500), nullable=True)          # Link đề án tuyển sinh chính thức
    is_latest = Column(Boolean, default=True)

    program = relationship("Program", back_populates="criteria")


# ==========================================
# 5. CAREER & MARKET DOMAIN
# ==========================================
class Career(Base):
    __tablename__ = "careers"

    career_id = Column(String(50), primary_key=True)
    title = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True, index=True)  # Đồng bộ thuộc tính name
    domain = Column(String(100), nullable=False)
    holland_codes = Column(JSON, default=list)  # ["RIA", "RIC", ...]
    description = Column(Text, nullable=True)
    job_growth_rate = Column(Float, default=0.0)
    salary_entry = Column(Integer, default=0)
    salary_mid = Column(Integer, default=0)
    entry_salary_avg = Column(Float, default=0.0)    # Đồng bộ thuộc tính
    senior_salary_avg = Column(Float, default=0.0)   # Đồng bộ thuộc tính
    top_companies = Column(JSON, default=list)
    hiring_companies = Column(JSON, default=list)   # Đồng bộ thuộc tính
    skills = Column(JSON, default=list)

    programs = relationship("Program", back_populates="career")

    @property
    def career_name(self) -> str:
        return self.name or self.title

    @property
    def target_hiring_companies(self) -> list:
        return self.hiring_companies or self.top_companies or []


# ==========================================
# 6. RECOMMENDATION, AUDIT & AI LOG DOMAIN
# ==========================================
class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"

    run_id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=True, index=True)
    profile_version = Column(Integer, default=1)
    rule_version = Column(String(50), default="deterministic_v2")
    input_params = Column(JSON, nullable=False)
    results = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("StudentProfile", back_populates="recommendation_runs")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    owner_user_id = Column(String(36), ForeignKey("users.user_id"), nullable=True, index=True)

    session_id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), default="Tư vấn hướng nghiệp", nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("StudentProfile", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    evidence = Column(JSON, default=list)     # trích dẫn nguồn
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ChatSession", back_populates="messages")


class QueryLog(Base):
    __tablename__ = "query_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(36), nullable=True)
    query_text = Column(Text, nullable=False)
    result_count = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

