"""SQLAlchemy database models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, String, Text, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class User(Base):
    """User model for Google OAuth users."""
    
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        index=True
    )
    google_sub: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        index=True
    )
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


class SystemAccount(Base):
    """System account model for service-to-service authentication."""
    
    __tablename__ = "system_accounts"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        index=True
    )
    secret_key_hash: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<SystemAccount(id={self.id}, username={self.username})>"


class PreAuthSession(Base):
    """Pre-authentication session for onboarding new users."""
    
    __tablename__ = "pre_auth_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    google_sub: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        index=True
    )
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<PreAuthSession(id={self.id}, google_sub={self.google_sub})>"
