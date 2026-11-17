"""
Auth Service: User Registration, Authentication and Dependency Injection.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models_db import User, StudentProfile, StudentBackground, AcademicProfile, HealthProfile
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from .schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse

security_scheme = HTTPBearer(auto_error=False)


def register_user(db: Session, req: RegisterRequest) -> TokenResponse:
    """Đăng ký tài khoản người dùng mới và khởi tạo hồ sơ học sinh mặc định."""
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được đăng ký trên hệ thống."
        )

    # Tạo User
    user = User(
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        role="student",
        is_active=True
    )
    db.add(user)
    db.flush()

    # Tạo StudentProfile liên kết
    profile = StudentProfile(
        student_id=user.user_id,
        first_name=req.first_name,
        last_name=req.last_name,
        gender=req.gender,
        grade_level=req.grade_level,
        target_year=req.target_year
    )
    db.add(profile)

    # Khởi tạo background, academic, health rỗng sẵn sàng
    bg = StudentBackground(student_id=user.user_id)
    academic = AcademicProfile(student_id=user.user_id)
    health = HealthProfile(student_id=user.user_id)
    db.add_all([bg, academic, health])

    db.commit()

    token = create_access_token(subject=user.user_id, role=user.role)
    return TokenResponse(
        access_token=token,
        user_id=user.user_id,
        role=user.role,
        email=user.email,
        name=f"{req.last_name} {req.first_name}"
    )


def authenticate_user(db: Session, req: LoginRequest) -> TokenResponse:
    """Xác thực đăng nhập và trả về JWT Bearer token."""
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị tạm khóa."
        )

    profile = db.query(StudentProfile).filter(StudentProfile.student_id == user.user_id).first()
    full_name = f"{profile.last_name} {profile.first_name}" if profile else user.email

    token = create_access_token(subject=user.user_id, role=user.role)
    return TokenResponse(
        access_token=token,
        user_id=user.user_id,
        role=user.role,
        email=user.email,
        name=full_name
    )


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dependency trích xuất và xác minh người dùng hiện tại từ token Bearer."""
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu xác thực tài khoản (Token không được cung cấp)."
        )

    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn."
        )

    user_id = payload["sub"]
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại hoặc tài khoản đã bị vô hiệu hóa."
        )
    return user


def get_current_user_optional(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency linh hoạt: trả về User nếu có token hợp lệ, hoặc None nếu là khách ẩn danh."""
    if not auth or not auth.credentials:
        return None
    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        return None
    return db.query(User).filter(User.user_id == payload["sub"], User.is_active == True).first()

