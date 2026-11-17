"""
Auth Router: Endpoints for Registration, Login, and Profile Me.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models_db import User, StudentProfile
from .schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse, AdminLoginRequest
from .service import register_user, authenticate_user, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Đăng ký tài khoản học sinh mới"""
    return register_user(db, req)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Đăng nhập hệ thống và nhận JWT Access Token"""
    return authenticate_user(db, req)


@router.post("/admin-login", response_model=TokenResponse)
def admin_login(req: AdminLoginRequest, db: Session = Depends(get_db)):
    """Password-only sign-in for the dedicated administrator account."""
    account = db.query(User).filter(
        User.email == "owner@foryourfuture.edu.vn", User.role == "admin"
    ).first()
    if not account:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Mật khẩu quản trị không chính xác.")
    return authenticate_user(db, LoginRequest(email=account.email, password=req.password))


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lấy thông tin người dùng hiện tại"""
    profile = db.query(StudentProfile).filter(StudentProfile.student_id == user.user_id).first()
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        first_name=profile.first_name if profile else None,
        last_name=profile.last_name if profile else None,
        grade_level=profile.grade_level if profile else None,
        target_year=profile.target_year if profile else None,
    )

