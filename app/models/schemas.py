"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field, field_validator
from typing import Literal
import re


# ============================================================================
# Google OAuth Schemas
# ============================================================================

class GoogleOAuthRequest(BaseModel):
    """Request body for Google OAuth callback."""
    code: str = Field(..., description="Authorization code from Google")
    code_verifier: str = Field(..., description="PKCE code verifier")


class UserInfo(BaseModel):
    """User information in response."""
    sub: str = Field(..., description="User ID (UUID)")
    nickname: str = Field(..., description="Username")
    role: Literal["user", "system"] = Field(..., description="User role")
    email: str | None = Field(None, description="User email")
    name: str | None = Field(None, description="User full name")


class AuthenticatedResponse(BaseModel):
    """Response when user is successfully authenticated."""
    status: Literal["AUTHENTICATED"] = "AUTHENTICATED"
    access_token: str = Field(..., description="JWT access token")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserInfo


class OnboardingUserInfo(BaseModel):
    """User information for onboarding."""
    email: str | None = Field(None, description="User email")
    name: str | None = Field(None, description="User full name from Google")


class OnboardingRequiredResponse(BaseModel):
    """Response when user needs to complete onboarding."""
    status: Literal["ONBOARDING_REQUIRED"] = "ONBOARDING_REQUIRED"
    pre_auth_token: str = Field(..., description="Pre-auth token (UUID)")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    next_step: Literal["SET_USERNAME"] = "SET_USERNAME"
    user_info: OnboardingUserInfo


# ============================================================================
# Onboarding Schemas
# ============================================================================

class SetUsernameRequest(BaseModel):
    """Request body for setting username during onboarding."""
    username: str = Field(..., min_length=3, max_length=30, description="Desired username")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must contain only letters, numbers, underscores, and hyphens')
        return v


class OnboardingStateResponse(BaseModel):
    """Response for onboarding state check."""
    step: Literal["SET_USERNAME"] = "SET_USERNAME"
    expires_in: int = Field(..., description="Remaining time in seconds")


# ============================================================================
# System Account Schemas
# ============================================================================

class SystemLoginRequest(BaseModel):
    """Request body for system account login."""
    username: str = Field(..., description="System account username")
    secret_key: str = Field(..., description="System account secret key")


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response."""
    status: Literal["ERROR"] = "ERROR"
    error: str = Field(..., description="Error code")
    detail: str | None = Field(None, description="Error details")


# ============================================================================
# Kafka Message Schemas
# ============================================================================

class NewUserKafkaMessage(BaseModel):
    """Kafka message for new user creation."""
    id: str = Field(..., description="User ID (UUID as string)")
    username: str = Field(..., description="Username")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
