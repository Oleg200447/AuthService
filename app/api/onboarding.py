"""Onboarding endpoints for new users."""
import logging
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.database import User, PreAuthSession
from app.models.schemas import (
    SetUsernameRequest,
    AuthenticatedResponse,
    OnboardingStateResponse,
    UserInfo,
)
from app.core.security import create_user_token
from app.core.kafka_producer import kafka_producer
from app.exceptions import (
    UsernameAlreadyTakenException,
    PreAuthTokenExpiredException,
    PreAuthTokenNotFoundException,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth/onboarding", tags=["Onboarding"])


async def get_pre_auth_session(
    authorization: str,
    db: AsyncSession
) -> PreAuthSession:
    """
    Validate and get pre-auth session from Authorization header.
    
    Args:
        authorization: Authorization header value (format: "PreAuth <token>")
        db: Database session
        
    Returns:
        PreAuthSession object
        
    Raises:
        PreAuthTokenNotFoundException: If token is invalid or not found
        PreAuthTokenExpiredException: If token is expired
    """
    # Parse authorization header
    if not authorization or not authorization.startswith("PreAuth "):
        logger.warning("Invalid authorization header format")
        raise PreAuthTokenNotFoundException()
    
    token = authorization.replace("PreAuth ", "").strip()
    
    # Validate UUID format
    try:
        token_uuid = uuid.UUID(token)
    except ValueError:
        logger.warning(f"Invalid UUID format: {token}")
        raise PreAuthTokenNotFoundException()
    
    # Get pre-auth session
    result = await db.execute(
        select(PreAuthSession).where(PreAuthSession.id == token_uuid)
    )
    pre_auth = result.scalar_one_or_none()
    
    if not pre_auth:
        logger.warning(f"Pre-auth session not found: {token}")
        raise PreAuthTokenNotFoundException()
    
    # Check expiration
    if pre_auth.expires_at < datetime.now(timezone.utc):
        logger.warning(f"Pre-auth session expired: {token}")
        raise PreAuthTokenExpiredException()
    
    return pre_auth


@router.post(
    "/username",
    response_model=AuthenticatedResponse,
    status_code=status.HTTP_200_OK,
    summary="Set username during onboarding",
    description="Complete user onboarding by setting a unique username"
)
async def set_username(
    request: SetUsernameRequest,
    authorization: str = Header(..., description="PreAuth token"),
    db: AsyncSession = Depends(get_db)
) -> AuthenticatedResponse:
    """
    Complete onboarding by setting username.
    
    Flow:
    1. Validate pre-auth token
    2. Check username uniqueness
    3. Create new user
    4. Delete pre-auth session
    5. Send Kafka message
    6. Return JWT token
    """
    logger.info(f"Setting username: {request.username}")
    
    # Step 1: Validate pre-auth token
    pre_auth = await get_pre_auth_session(authorization, db)
    
    # Step 2: Check username uniqueness
    result = await db.execute(
        select(User).where(User.username == request.username)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        logger.warning(f"Username already taken: {request.username}")
        raise UsernameAlreadyTakenException()
    
    # Step 3: Create new user
    new_user = User(
        username=request.username,
        google_sub=pre_auth.google_sub,
        email=pre_auth.email,
        name=pre_auth.name
    )
    db.add(new_user)
    
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        logger.error(f"Database integrity error - username may be taken: {request.username}")
        raise UsernameAlreadyTakenException()
    
    logger.info(f"Created new user: {new_user.id} - {new_user.username}")
    
    # Step 4: Delete pre-auth session
    await db.delete(pre_auth)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info(f"Deleted pre-auth session: {pre_auth.id}")
    
    # Step 5: Send Kafka message
    created_at_iso = new_user.created_at.isoformat()
    
    kafka_success = await kafka_producer.send_new_user_message(
        user_id=str(new_user.id),
        username=new_user.username,
        created_at=created_at_iso
    )
    
    if not kafka_success:
        logger.error(f"Failed to send Kafka message for user: {new_user.id}")
    
    # Step 6: Generate JWT token
    token, expires_in = create_user_token(
        user_id=str(new_user.id),
        username=new_user.username,
        role="user"
    )
    
    return AuthenticatedResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserInfo(
            sub=str(new_user.id),
            nickname=new_user.username,
            role="user",
            email=new_user.email,
            name=new_user.name
        )
    )


@router.get(
    "/state",
    response_model=OnboardingStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Get onboarding state",
    description="Check the current state of onboarding process"
)
async def get_onboarding_state(
    authorization: str = Header(..., description="PreAuth token"),
    db: AsyncSession = Depends(get_db)
) -> OnboardingStateResponse:
    """
    Get onboarding state.
    
    Returns information about the current onboarding step and remaining time.
    """
    logger.info("Checking onboarding state")
    
    # Validate pre-auth token
    pre_auth = await get_pre_auth_session(authorization, db)
    
    # Calculate remaining time
    expires_in = int((pre_auth.expires_at - datetime.now(timezone.utc)).total_seconds())
    
    return OnboardingStateResponse(
        step="SET_USERNAME",
        expires_in=max(0, expires_in)
    )
