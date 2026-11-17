"""
University and Program Schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ProgramCriteriaItem(BaseModel):
    criteria_id: str
    year: int
    method: str
    group_code: Optional[str] = None
    benchmark_score: Optional[float] = None
    minimum_threshold: Optional[float] = None
    score_scale: Optional[float]
    raw_score: Optional[str] = None
    quota: Optional[int] = None
    min_height_male: Optional[float] = None
    min_height_female: Optional[float] = None
    max_eye_degree: Optional[float] = None
    gender_requirement: str = "Any"
    source_url: Optional[str] = None


class ProgramDetailItem(BaseModel):
    program_id: str
    uni_id: str
    major_code: str
    name: str
    degree_level: Optional[str]
    duration_years: Optional[float]
    tuition_annual: Optional[int]
    effective_cost: Optional[int]
    is_subsidized: bool
    faculty_ratio: Optional[float] = None
    facilities: List[str] = []
    career_id: Optional[str] = None
    career_title: Optional[str] = None
    criteria: List[ProgramCriteriaItem] = []


class UniversityListItem(BaseModel):
    uni_id: str
    name: str
    short_name: Optional[str] = None
    code: Optional[str] = None
    type: str
    location: str
    region: str
    ranking_national: Optional[int] = None
    website: Optional[str] = None
    admissions_url: Optional[str] = None
    has_dormitory: bool
    logo: Optional[str] = None
    focus_riasec: List[str] = []
    program_count: int = 0


class UniversityDetailResponse(BaseModel):
    uni_id: str
    name: str
    short_name: Optional[str] = None
    code: Optional[str] = None
    type: str
    location: str
    region: str
    ranking_national: Optional[int] = None
    website: Optional[str] = None
    admissions_url: Optional[str] = None
    has_dormitory: bool
    logo: Optional[str] = None
    focus_riasec: List[str] = []
    programs: List[ProgramDetailItem] = []
