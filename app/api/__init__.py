"""API package."""
from app.api.auth import router as auth_router
from app.api.onboarding import router as onboarding_router
from app.api.system import router as system_router

__all__ = ["auth_router", "onboarding_router", "system_router"]
