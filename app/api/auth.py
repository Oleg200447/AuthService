"""Google OAuth authentication endpoints."""
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.database import User, PreAuthSession
from app.models.schemas import (
    GoogleOAuthRequest,
    AuthenticatedResponse,
    OnboardingRequiredResponse,
    UserInfo,
    OnboardingUserInfo,
)
from app.core.security import create_user_token
from app.core.google_oauth import google_oauth_client
from app.exceptions import GoogleOAuthException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth/oauth", tags=["OAuth"])


@router.post(
    "/google",
    response_model=AuthenticatedResponse | OnboardingRequiredResponse,
    status_code=status.HTTP_200_OK,
    summary="Google OAuth callback",
    description="Exchange Google authorization code for JWT token or initiate onboarding"
)
async def google_oauth_callback(
    request: GoogleOAuthRequest,
    db: AsyncSession = Depends(get_db)
) -> AuthenticatedResponse | OnboardingRequiredResponse:
    """
    Handle Google OAuth callback.
    
    Flow:
    1. Exchange authorization code for tokens
    2. Decode ID token to get user claims
    3. Check if user exists by google_sub
    4. If exists: return JWT token
    5. If not exists: create pre-auth session and return onboarding response
    """
    logger.info("Processing Google OAuth callback")
    
    # Step 1: Exchange code for tokens
    tokens = await google_oauth_client.exchange_code_for_tokens(
        code=request.code,
        code_verifier=request.code_verifier
    )
    
    if not tokens or "id_token" not in tokens:
        logger.error("Failed to exchange code for tokens")
        raise GoogleOAuthException("Failed to exchange authorization code")
    
    # Step 2: Decode ID token
    id_token_claims = google_oauth_client.decode_id_token(tokens["id_token"])
    
    if not id_token_claims:
        logger.error("Failed to decode ID token")
        raise GoogleOAuthException("Failed to decode ID token")
    
    google_sub = id_token_claims.get("sub")
    email = id_token_claims.get("email")
    name = id_token_claims.get("name")
    
    if not google_sub:
        logger.error("No 'sub' claim in ID token")
        raise GoogleOAuthException("Invalid ID token: missing 'sub' claim")
    
    logger.info(f"Google OAuth successful for sub: {google_sub}")
    
    # Step 3: Check if user exists
    result = await db.execute(
        select(User).where(User.google_sub == google_sub)
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Step 4: User exists - return JWT
        logger.info(f"User found: {user.username}")
        
        token, expires_in = create_user_token(
            user_id=str(user.id),
            username=user.username,
            role="user"
        )
        
        return AuthenticatedResponse(
            access_token=token,
            expires_in=expires_in,
            user=UserInfo(
                sub=str(user.id),
                nickname=user.username,
                role="user",
                email=user.email,
                name=user.name
            )
        )
    
    # Step 5: User doesn't exist - create pre-auth session
    logger.info(f"New user - creating pre-auth session for sub: {google_sub}")
    
    # Check if pre-auth session already exists
    result = await db.execute(
        select(PreAuthSession).where(PreAuthSession.google_sub == google_sub)
    )
    pre_auth = result.scalar_one_or_none()
    
    if pre_auth:
        # Update existing session
        pre_auth.email = email
        pre_auth.name = name
        pre_auth.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        logger.info(f"Updated existing pre-auth session: {pre_auth.id}")
    else:
        # Create new session
        pre_auth = PreAuthSession(
            google_sub=google_sub,
            email=email,
            name=name,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
        )
        db.add(pre_auth)
        logger.info(f"Created new pre-auth session: {pre_auth.id}")
    
    await db.commit()
    await db.refresh(pre_auth)
    
    # Calculate remaining time
    expires_in = int((pre_auth.expires_at - datetime.now(timezone.utc)).total_seconds())
    
    return OnboardingRequiredResponse(
        pre_auth_token=str(pre_auth.id),
        expires_in=max(0, expires_in),
        user_info=OnboardingUserInfo(
            email=email,
            name=name
        )
    )
