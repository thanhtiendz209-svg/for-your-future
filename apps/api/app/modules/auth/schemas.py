"""
Auth Schemas for Pydantic v2.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class PasswordRequest(BaseModel):
    password: str

    @field_validator("password", mode="before")
    @classmethod
    def ignore_password_spaces(cls, value):
        return "".join(value.split()) if isinstance(value, str) else value


class RegisterRequest(PasswordRequest):
    email: str = Field(..., min_length=3, description="Email tài khoản")
    password: str = Field(..., min_length=6, description="Mật khẩu tối thiểu 6 ký tự")
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    grade_level: int = Field(12, ge=10, le=12)
    target_year: int = Field(2026, ge=2024, le=2030)
    gender: str = Field("Other")


class LoginRequest(PasswordRequest):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    email: str
    name: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    grade_level: Optional[int] = None
    target_year: Optional[int] = None


class AdminLoginRequest(PasswordRequest):
    pass
