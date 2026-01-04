"""System account authentication endpoints."""
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.database import SystemAccount
from app.models.schemas import (
    SystemLoginRequest,
    AuthenticatedResponse,
    UserInfo,
)
from app.core.security import verify_password, create_user_token
from app.exceptions import InvalidCredentialsException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth/system", tags=["System Accounts"])


@router.post(
    "/login",
    response_model=AuthenticatedResponse,
    status_code=status.HTTP_200_OK,
    summary="System account login",
    description="Authenticate a system account and receive a JWT token"
)
async def system_login(
    request: SystemLoginRequest,
    db: AsyncSession = Depends(get_db)
) -> AuthenticatedResponse:
    """
    System account login.
    
    Flow:
    1. Find system account by username
    2. Verify secret key
    3. Check if account is active
    4. Generate JWT token
    """
    logger.info(f"System login attempt: {request.username}")
    
    # Step 1: Find system account
    result = await db.execute(
        select(SystemAccount).where(SystemAccount.username == request.username)
    )
    system_account = result.scalar_one_or_none()
    
    if not system_account:
        logger.warning(f"System account not found: {request.username}")
        raise InvalidCredentialsException()
    
    # Step 2: Verify secret key
    if not verify_password(request.secret_key, system_account.secret_key_hash):
        logger.warning(f"Invalid secret key for system account: {request.username}")
        raise InvalidCredentialsException()
    
    # Step 3: Check if active
    if not system_account.active:
        logger.warning(f"Inactive system account: {request.username}")
        raise InvalidCredentialsException()
    
    logger.info(f"System account authenticated: {request.username}")
    
    # Step 4: Generate JWT token
    token, expires_in = create_user_token(
        user_id=str(system_account.id),
        username=system_account.username,
        role="system"
    )
    
    return AuthenticatedResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserInfo(
            sub=str(system_account.id),
            nickname=system_account.username,
            role="system"
        )
    )
