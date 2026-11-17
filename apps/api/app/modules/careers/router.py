"""
Career Router.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from .schemas import CareerListItem, CareerDetailResponse
from .service import list_careers, get_career_detail, get_careers_by_holland

router = APIRouter(prefix="/careers", tags=["Careers"])


@router.get("", response_model=List[CareerListItem])
def get_careers(
    domain: Optional[str] = Query(None, description="Lọc theo lĩnh vực ngành nghề"),
    q: Optional[str] = Query(None, description="Tìm kiếm nghề theo từ khóa"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Khám phá danh mục ngành nghề, mức lương và xu hướng việc làm"""
    return list_careers(db, domain, q, skip, limit)


@router.get("/{career_id}", response_model=CareerDetailResponse)
def get_career(career_id: str, db: Session = Depends(get_db)):
    """Xem chi tiết yêu cầu năng lực, kỹ năng và các trường đại học đào tạo"""
    return get_career_detail(db, career_id)


@router.get("/by-holland/{code}", response_model=List[CareerListItem])
def get_careers_for_holland(code: str, db: Session = Depends(get_db)):
    """Tìm danh sách nghề nghiệp phù hợp với mã tổ hợp 3 ký tự Holland RIASEC"""
    return get_careers_by_holland(db, code)

