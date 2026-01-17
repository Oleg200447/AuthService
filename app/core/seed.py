"""System accounts seeding functionality."""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.database import SystemAccount
from app.core.security import hash_system_secret
from app.config import settings

logger = logging.getLogger(__name__)


async def seed_system_accounts():
    """Create system accounts if they don't exist.
    
    This function is idempotent - it can be run multiple times safely.
    It will only create accounts that don't already exist in the database.
    """
    system_accounts_config = [
        {"username": "system_1", "secret": settings.SYSTEM_1_SECRET},
        {"username": "system_2", "secret": settings.SYSTEM_2_SECRET},
        {"username": "system_3", "secret": settings.SYSTEM_3_SECRET},
        {"username": "system_4", "secret": settings.SYSTEM_4_SECRET},
        {"username": "system_5", "secret": settings.SYSTEM_5_SECRET},
    ]
    
    try:
        async with AsyncSessionLocal() as session:
            accounts_created = 0
            accounts_existing = 0
            
            for account_config in system_accounts_config:
                username = account_config["username"]
                secret = account_config["secret"]
                
                # Check if account already exists
                result = await session.execute(
                    select(SystemAccount).where(SystemAccount.username == username)
                )
                existing_account = result.scalar_one_or_none()
                
                if existing_account:
                    accounts_existing += 1
                    logger.debug(f"System account '{username}' already exists")
                    continue
                
                # Create new system account
                secret_hash = hash_system_secret(secret)
                new_account = SystemAccount(
                    username=username,
                    secret_key_hash=secret_hash,
                    active=True
                )
                
                session.add(new_account)
                accounts_created += 1
                logger.info(f"Created system account '{username}'")
            
            await session.commit()
            
            if accounts_created > 0:
                logger.info(f"System accounts seeding completed: {accounts_created} created, {accounts_existing} already existed")
            else:
                logger.debug(f"System accounts seeding completed: all {accounts_existing} accounts already exist")
                
    except Exception as e:
        logger.error(f"Error during system accounts seeding: {e}", exc_info=True)
        raise
