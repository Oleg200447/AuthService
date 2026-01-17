"""Seed system accounts into the database.

This script should be run after the initial migration to create system accounts.
It's idempotent - can be run multiple times safely.

Usage:
    python scripts/seed_system_accounts.py
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_maker
from app.models.database import SystemAccount
from app.core.security import hash_system_secret
from app.config import settings


async def seed_system_accounts():
    """Create system accounts if they don't exist."""
    
    system_accounts_config = [
        {"username": "system_1", "secret": settings.SYSTEM_1_SECRET},
        {"username": "system_2", "secret": settings.SYSTEM_2_SECRET},
        {"username": "system_3", "secret": settings.SYSTEM_3_SECRET},
        {"username": "system_4", "secret": settings.SYSTEM_4_SECRET},
        {"username": "system_5", "secret": settings.SYSTEM_5_SECRET},
    ]
    
    async with async_session_maker() as session:
        for account_config in system_accounts_config:
            username = account_config["username"]
            secret = account_config["secret"]
            
            # Check if account already exists
            result = await session.execute(
                select(SystemAccount).where(SystemAccount.username == username)
            )
            existing_account = result.scalar_one_or_none()
            
            if existing_account:
                print(f"✓ System account '{username}' already exists, skipping...")
                continue
            
            # Create new system account
            secret_hash = hash_system_secret(secret)
            new_account = SystemAccount(
                username=username,
                secret_key_hash=secret_hash,
                active=True
            )
            
            session.add(new_account)
            print(f"✓ Created system account '{username}'")
        
        await session.commit()
        print("\n✅ System accounts seeding completed successfully!")


async def main():
    """Main entry point."""
    try:
        print("🌱 Starting system accounts seeding...\n")
        await seed_system_accounts()
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
