"""
University Router.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from .schemas import UniversityListItem, UniversityDetailResponse, ProgramDetailItem
from .service import list_universities, get_university_detail, get_programs_by_major_code

router = APIRouter(prefix="/universities", tags=["Universities"])


@router.get("", response_model=List[UniversityListItem])
def get_universities(
    q: Optional[str] = Query(None, description="Tìm kiếm theo tên trường, mã trường, địa điểm"),
    region: Optional[str] = Query(None, description="Miền Bắc, Miền Trung, Miền Nam"),
    location: Optional[str] = Query(None, description="Tỉnh/Thành phố"),
    riasec: Optional[str] = Query(None, description="Nhóm RIASEC trọng tâm"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Tra cứu danh sách 126 trường Đại học toàn quốc với bộ lọc đa tiêu chí"""
    return list_universities(db, q, region, location, riasec, skip, limit)


@router.get("/{uni_id}", response_model=UniversityDetailResponse)
def get_university(uni_id: str, db: Session = Depends(get_db)):
    """Xem thông tin chi tiết của một trường (URL uni-xxx) và các ngành đào tạo"""
    return get_university_detail(db, uni_id)


@router.get("/{uni_id}/programs", response_model=List[ProgramDetailItem])
def get_university_programs(
    uni_id: str,
    nganh: Optional[str] = Query(None, description="Lọc chính xác theo mã ngành (ví dụ: ?nganh=7480201)"),
    db: Session = Depends(get_db)
):
    """Lọc chương trình đào tạo của trường theo mã ngành chính xác"""
    return get_programs_by_major_code(db, uni_id, nganh)
