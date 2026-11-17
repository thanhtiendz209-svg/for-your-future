"""
Career Service.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.models_db import Career, Program, University
from .schemas import CareerListItem, CareerDetailResponse


def list_careers(
    db: Session,
    domain: Optional[str] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[CareerListItem]:
    query = db.query(Career)
    if domain:
        query = query.filter(Career.domain == domain)
    if q:
        query = query.filter(Career.title.ilike(f"%{q.strip()}%"))

    careers = query.order_by(Career.job_growth_rate.desc()).offset(skip).limit(limit).all()
    return [
        CareerListItem(
            career_id=c.career_id,
            title=c.title,
            domain=c.domain,
            holland_codes=c.holland_codes or [],
            job_growth_rate=c.job_growth_rate,
            salary_entry=c.salary_entry,
            salary_mid=c.salary_mid,
            top_companies=c.top_companies or [],
            skills=c.skills or [],
        )
        for c in careers
    ]


def get_career_detail(db: Session, career_id: str) -> CareerDetailResponse:
    c = db.query(Career).filter(Career.career_id == career_id).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy nghề với mã {career_id}")

    progs = db.query(Program).filter(Program.career_id == career_id).all()
    prog_data = []
    for p in progs:
        u = db.query(University).filter(University.uni_id == p.uni_id).first()
        prog_data.append({
            "program_id": p.program_id,
            "program_name": p.name,
            "university_name": u.name if u else p.uni_id,
            "uni_id": p.uni_id,
            "major_code": p.major_code,
            "effective_cost": p.effective_cost,
        })

    return CareerDetailResponse(
        career_id=c.career_id,
        title=c.title,
        domain=c.domain,
        holland_codes=c.holland_codes or [],
        description=c.description,
        job_growth_rate=c.job_growth_rate,
        salary_entry=c.salary_entry,
        salary_mid=c.salary_mid,
        top_companies=c.top_companies or [],
        skills=c.skills or [],
        related_programs=prog_data,
    )


def get_careers_by_holland(db: Session, holland_code: str) -> List[CareerListItem]:
    code = holland_code.strip().upper()
    primary = code[0] if len(code) > 0 else ""
    careers = db.query(Career).all()
    matched = []
    for c in careers:
        codes = c.holland_codes or []
        # Khớp chính xác 3 chữ cái hoặc chứa chữ cái chính
        if code in codes or any(primary in cd for cd in codes):
            matched.append(
                CareerListItem(
                    career_id=c.career_id,
                    title=c.title,
                    domain=c.domain,
                    holland_codes=c.holland_codes or [],
                    job_growth_rate=c.job_growth_rate,
                    salary_entry=c.salary_entry,
                    salary_mid=c.salary_mid,
                    top_companies=c.top_companies or [],
                    skills=c.skills or [],
                )
            )
    return matched

