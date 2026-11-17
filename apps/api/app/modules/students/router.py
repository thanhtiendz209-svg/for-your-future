"""
Student Router: Endpoints for Profile, Academic, Background, Health, and Local Import.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models_db import User
from app.modules.auth.service import get_current_user
from .schemas import (
    StudentProfileUpdate,
    BackgroundUpdate,
    AcademicUpdate,
    HealthUpdate,
    FullStudentResponse,
    ImportLocalProfileRequest,
)
from .service import (
    get_full_student_profile,
    update_student_profile,
    update_student_background,
    update_academic_profile,
    update_health_profile,
    import_local_profile,
)

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/profile", response_model=FullStudentResponse)
def get_my_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lấy toàn bộ hồ sơ chi tiết (cá nhân, học tập, sức khỏe, tài chính, bài test) của học sinh."""
    return get_full_student_profile(db, user.user_id)


@router.put("/profile", response_model=FullStudentResponse)
def update_profile(
    req: StudentProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cập nhật thông tin cá nhân cơ bản"""
    return update_student_profile(db, user.user_id, req)


@router.put("/background", response_model=FullStudentResponse)
def update_background(
    req: BackgroundUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cập nhật điều kiện tài chính, khu vực ưu tiên và đối tượng chính sách"""
    return update_student_background(db, user.user_id, req)


@router.put("/academic", response_model=FullStudentResponse)
def update_academic(
    req: AcademicUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cập nhật kết quả học tập (GPA các lớp, điểm thi, chứng chỉ IELTS/SAT)"""
    return update_academic_profile(db, user.user_id, req)


@router.put("/health", response_model=FullStudentResponse)
def update_health(
    req: HealthUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cập nhật thể lực và sức khỏe (phục vụ sơ tuyển Quân đội, Công an, Hàng không)"""
    return update_health_profile(db, user.user_id, req)


@router.post("/import-local", response_model=FullStudentResponse)
def import_local(
    req: ImportLocalProfileRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Đồng bộ dữ liệu khách từ localStorage vào tài khoản học sinh đã đăng nhập"""
    return import_local_profile(db, user.user_id, req)
