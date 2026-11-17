"""
Student Domain Schemas.
"""

from typing import Optional, Dict, Any, List
from datetime import date
from pydantic import BaseModel, Field


class StudentProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    current_school: Optional[str] = None
    grade_level: Optional[int] = Field(None, ge=10, le=12)
    target_year: Optional[int] = Field(None, ge=2024, le=2030)


class BackgroundUpdate(BaseModel):
    hometown_province: Optional[str] = None  # Quê quán / tỉnh thành học THPT
    income_level: Optional[str] = None
    max_annual_tuition: Optional[int] = Field(None, ge=0)
    priority_zone: Optional[str] = None      # KV1, KV2-NT, KV2, KV3
    priority_object: Optional[str] = None    # 01..07, None
    financial_hardship: Optional[bool] = None


class AcademicUpdate(BaseModel):
    gpa_grade_10: Optional[float] = Field(None, ge=0.0, le=10.0)
    gpa_grade_11: Optional[float] = Field(None, ge=0.0, le=10.0)
    gpa_grade_12: Optional[float] = Field(None, ge=0.0, le=10.0)
    gpa_5_semesters: Optional[float] = Field(None, ge=0.0, le=10.0)
    academic_rank: Optional[str] = None
    conduct_grade_10: Optional[str] = None
    conduct_grade_11: Optional[str] = None
    conduct_grade_12: Optional[str] = None
    ielts_score: Optional[float] = Field(None, ge=0.0, le=9.0)
    sat_score: Optional[int] = Field(None, ge=400, le=1600)
    dgnl_hcm_score: Optional[int] = Field(None, ge=0, le=1200)  # ĐGNL ĐHQG TP.HCM
    dgnl_hn_score: Optional[int] = Field(None, ge=0, le=150)    # ĐGNL ĐHQG Hà Nội
    tsa_hust_score: Optional[float] = Field(None, ge=0.0, le=100.0)  # ĐGTD ĐH Bách khoa Hà Nội
    subject_scores: Optional[Dict[str, float]] = None
    exam_scores: Optional[Dict[str, float]] = None


class HealthUpdate(BaseModel):
    height_cm: Optional[float] = Field(None, ge=100.0, le=250.0)
    weight_kg: Optional[float] = Field(None, ge=30.0, le=200.0)
    eye_degree_left: Optional[float] = Field(None, ge=0.0, le=20.0)
    eye_degree_right: Optional[float] = Field(None, ge=0.0, le=20.0)
    color_blindness: Optional[bool] = None
    hearing_status: Optional[str] = None
    has_health_certificate: Optional[bool] = None


class FullStudentResponse(BaseModel):
    student_id: str
    email: str
    first_name: str
    last_name: str
    dob: Optional[date] = None
    gender: str
    phone: Optional[str] = None
    current_school: Optional[str] = None
    grade_level: int
    target_year: int
    background: Dict[str, Any]
    academic: Dict[str, Any]
    health: Dict[str, Any]
    latest_riasec: Optional[Dict[str, Any]] = None
    latest_mbti: Optional[Dict[str, Any]] = None


class ImportLocalProfileRequest(BaseModel):
    """Đồng bộ dữ liệu từ localStorage của bản cũ sang tài khoản mới."""
    quiz_results: Optional[List[Dict[str, Any]]] = None
    academic: Optional[Dict[str, Any]] = None
    background: Optional[Dict[str, Any]] = None
    health: Optional[Dict[str, Any]] = None
