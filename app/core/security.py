"""Security utilities for JWT and password hashing."""
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings

# Password hashing context (for regular user passwords if needed)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# System accounts password context (for long secret keys, no 72-byte limit)
system_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_system_secret(secret: str) -> str:
    """Hash a system account secret using argon2."""
    return system_pwd_context.hash(secret)


def verify_system_secret(plain_secret: str, hashed_secret: str) -> bool:
    """Verify a system account secret against a hash."""
    return system_pwd_context.verify(plain_secret, hashed_secret)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None
) -> str:
    """Create JWT access token.
    
    Args:
        data: Dictionary containing token payload
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_user_token(user_id: str, username: str, role: str = "user") -> tuple[str, int]:
    """Create JWT token for a user.
    
    Args:
        user_id: User UUID as string
        username: Username
        role: User role (user or system)
        
    Returns:
        Tuple of (token, expires_in_seconds)
    """
    if role == "system":
        expires_delta = timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRE_SYSTEM)
        expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_SYSTEM
    else:
        expires_delta = timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRE_USER)
        expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_USER
    
    token_data = {
        "sub": user_id,
        "nickname": username,
        "role": role,
        "iss": "auth_service"
    }
    
    token = create_access_token(token_data, expires_delta)
    
    return token, expires_in


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and verify JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
