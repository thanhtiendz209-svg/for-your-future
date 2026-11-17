"""
Security, Password Hashing, and JWT Management.
Uses standard PBKDF2-HMAC-SHA256 for password hashing and PyJWT for bearer tokens.
"""

import hmac
import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
import jwt
from .config import settings


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 16-byte cryptographically secure salt."""
    salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256", 
        password.encode("utf-8"), 
        salt.encode("utf-8"), 
        100000
    ).hex()
    return f"{salt}${pw_hash}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against stored salt$hash format."""
    try:
        salt, expected_hash = hashed_password.split("$", 1)
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256", 
            plain_password.encode("utf-8"), 
            salt.encode("utf-8"), 
            100000
        ).hex()
        return hmac.compare_digest(expected_hash, actual_hash)
    except Exception:
        return False


def create_access_token(
    subject: Union[str, Any], 
    role: str = "student",
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generate signed JWT access token with user_id subject, role, and expiration."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT access token. Returns payload dict or None on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except Exception:
        return None

