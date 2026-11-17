"""
Career Schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class CareerListItem(BaseModel):
    career_id: str
    title: str
    domain: str
    holland_codes: List[str] = []
    job_growth_rate: float
    salary_entry: int
    salary_mid: int
    top_companies: List[str] = []
    skills: List[str] = []


class CareerDetailResponse(BaseModel):
    career_id: str
    title: str
    domain: str
    holland_codes: List[str] = []
    description: Optional[str] = None
    job_growth_rate: float
    salary_entry: int
    salary_mid: int
    top_companies: List[str] = []
    skills: List[str] = []
    related_programs: List[Dict[str, Any]] = []

