import json
"""
University and Program Service.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.core.models_db import University, Program, AdmissionCriteria, Career
from .schemas import (
    UniversityListItem,
    UniversityDetailResponse,
    ProgramDetailItem,
    ProgramCriteriaItem,
)


def list_universities(
    db: Session,
    q: Optional[str] = None,
    region: Optional[str] = None,
    location: Optional[str] = None,
    riasec: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[UniversityListItem]:
    query = db.query(University)

    if q:
        search = f"%{q.strip().lower()}%"
        query = query.filter(
            (University.name.ilike(search))
            | (University.short_name.ilike(search))
            | (University.code.ilike(search))
            | (University.location.ilike(search))
        )

    if region:
        query = query.filter(University.region == region)

    if location:
        query = query.filter(University.location.ilike(f"%{location.strip()}%"))

    unis = query.order_by(University.ranking_national.asc().nullslast(), University.uni_id.asc()).offset(skip).limit(limit).all()

    result = []
    for u in unis:
        prog_count = db.query(Program).filter(Program.uni_id == u.uni_id).count()
        result.append(
            UniversityListItem(
                uni_id=u.uni_id,
                name=u.name,
                short_name=u.short_name,
                code=u.code,
                type=u.type,
                location=u.location,
                region=u.region,
                ranking_national=u.ranking_national,
                website=u.website,
                admissions_url=u.admissions_url,
                has_dormitory=u.has_dormitory,
                logo=u.logo,
                focus_riasec=u.focus_riasec or [],
                program_count=prog_count,
            )
        )
    return result


def get_university_detail(db: Session, uni_id: str) -> UniversityDetailResponse:
    u = db.query(University).filter(University.uni_id == uni_id).first()
    if not u:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy trường với mã {uni_id}")

    programs = (
        db.query(Program)
        .filter(Program.uni_id == uni_id)
        .options(joinedload(Program.criteria), joinedload(Program.career))
        .all()
    )

    prog_items = []
    for p in programs:
        criteria_items = [
            ProgramCriteriaItem(
                criteria_id=c.criteria_id,
                year=c.year,
                method=c.method,
                group_code=c.group_code,
                benchmark_score=c.benchmark_score,
                minimum_threshold=c.minimum_threshold,
                score_scale=(json.loads(c.special_conditions).get('scale_provided') if c.special_conditions and c.special_conditions.startswith('{') else c.score_scale),
                raw_score=(json.loads(c.special_conditions).get('raw') if c.special_conditions and c.special_conditions.startswith('{') else None),
                quota=c.quota,
                min_height_male=c.min_height_male,
                min_height_female=c.min_height_female,
                max_eye_degree=c.max_eye_degree,
                gender_requirement=c.gender_requirement,
                source_url=c.source_url,
            )
            for c in p.criteria
        ]

        prog_items.append(
            ProgramDetailItem(
                program_id=p.program_id,
                uni_id=p.uni_id,
                major_code=p.major_code,
                name=p.name,
                degree_level=p.degree_level,
                duration_years=p.duration_years,
                tuition_annual=p.tuition_annual,
                effective_cost=p.effective_cost,
                is_subsidized=p.is_subsidized,
                faculty_ratio=p.faculty_ratio,
                facilities=p.facilities or [],
                career_id=p.career_id,
                career_title=p.career.title if p.career else None,
                criteria=criteria_items,
            )
        )

    return UniversityDetailResponse(
        uni_id=u.uni_id,
        name=u.name,
        short_name=u.short_name,
        code=u.code,
        type=u.type,
        location=u.location,
        region=u.region,
        ranking_national=u.ranking_national,
        website=u.website,
        admissions_url=u.admissions_url,
        has_dormitory=u.has_dormitory,
        logo=u.logo,
        focus_riasec=u.focus_riasec or [],
        programs=prog_items,
    )


def get_programs_by_major_code(
    db: Session, uni_id: str, major_code: Optional[str] = None
) -> List[ProgramDetailItem]:
    """
    Lọc chính xác theo query ?nganh=CODE.
    Tuân thủ quy tắc Stage 1: Mã không có dữ liệu trả về mảng rỗng, không tự ghép tên gần giống.
    """
    query = (
        db.query(Program)
        .filter(Program.uni_id == uni_id)
        .options(joinedload(Program.criteria), joinedload(Program.career))
    )
    if major_code:
        query = query.filter(Program.major_code == major_code.strip())

    programs = query.all()
    prog_items = []
    for p in programs:
        crit_items = [
            ProgramCriteriaItem(
                criteria_id=c.criteria_id,
                year=c.year,
                method=c.method,
                group_code=c.group_code,
                benchmark_score=c.benchmark_score,
                minimum_threshold=c.minimum_threshold,
                score_scale=(json.loads(c.special_conditions).get('scale_provided') if c.special_conditions and c.special_conditions.startswith('{') else c.score_scale),
                raw_score=(json.loads(c.special_conditions).get('raw') if c.special_conditions and c.special_conditions.startswith('{') else None),
                quota=c.quota,
                min_height_male=c.min_height_male,
                min_height_female=c.min_height_female,
                max_eye_degree=c.max_eye_degree,
                gender_requirement=c.gender_requirement,
                source_url=c.source_url,
            )
            for c in p.criteria
        ]
        prog_items.append(
            ProgramDetailItem(
                program_id=p.program_id,
                uni_id=p.uni_id,
                major_code=p.major_code,
                name=p.name,
                degree_level=p.degree_level,
                duration_years=p.duration_years,
                tuition_annual=p.tuition_annual,
                effective_cost=p.effective_cost,
                is_subsidized=p.is_subsidized,
                faculty_ratio=p.faculty_ratio,
                facilities=p.facilities or [],
                career_id=p.career_id,
                career_title=p.career.title if p.career else None,
                criteria=crit_items,
            )
        )
    return prog_items
