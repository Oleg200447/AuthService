"""Custom exceptions for the application."""
from fastapi import HTTPException, status


class UsernameAlreadyTakenException(HTTPException):
    """Exception raised when username is already taken."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"status": "ERROR", "error": "USERNAME_TAKEN"}
        )


class InvalidCredentialsException(HTTPException):
    """Exception raised when credentials are invalid."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "ERROR", "error": "INVALID_CREDENTIALS"}
        )


class PreAuthTokenExpiredException(HTTPException):
    """Exception raised when pre-auth token is expired."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "ERROR", "error": "TOKEN_EXPIRED"}
        )


class PreAuthTokenNotFoundException(HTTPException):
    """Exception raised when pre-auth token is not found."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"status": "ERROR", "error": "TOKEN_NOT_FOUND"}
        )


class GoogleOAuthException(HTTPException):
    """Exception raised when Google OAuth fails."""
    
    def __init__(self, detail: str = "Google OAuth failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "ERROR", "error": "OAUTH_FAILED", "detail": detail}
        )
