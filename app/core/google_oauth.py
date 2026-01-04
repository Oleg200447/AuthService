"""Google OAuth client for authentication."""
import logging
from typing import Any
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

# Google OAuth endpoints
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


class GoogleOAuthClient:
    """Client for Google OAuth operations."""
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
    
    async def exchange_code_for_tokens(
        self,
        code: str,
        code_verifier: str,
        redirect_uri: str = "postmessage"
    ) -> dict[str, Any] | None:
        """Exchange authorization code for access and ID tokens.
        
        Args:
            code: Authorization code from Google
            code_verifier: PKCE code verifier
            redirect_uri: Redirect URI (default: postmessage for mobile/SPA)
            
        Returns:
            Dictionary with tokens or None on error
        """
        token_data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    GOOGLE_TOKEN_URL,
                    data=token_data,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(
                        f"Failed to exchange code for tokens: {response.status_code} - {response.text}"
                    )
                    return None
                
                return response.json()
        
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> dict[str, Any] | None:
        """Get user info from Google using access token.
        
        Args:
            access_token: Google access token
            
        Returns:
            Dictionary with user info or None on error
        """
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    GOOGLE_USERINFO_URL,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(
                        f"Failed to get user info: {response.status_code} - {response.text}"
                    )
                    return None
                
                return response.json()
        
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def decode_id_token(self, id_token: str) -> dict[str, Any] | None:
        """Decode and verify Google ID token.
        
        For production, this should use proper JWT verification with Google's public keys.
        For now, we'll use a simple decode without verification (NOT RECOMMENDED FOR PRODUCTION).
        
        Args:
            id_token: Google ID token (JWT)
            
        Returns:
            Dictionary with token claims or None on error
        """
        try:
            # In production, verify the token signature with Google's public keys
            # For now, we'll just decode it (this is insecure for production!)
            from jose import jwt
            
            # Decode without verification (INSECURE - for development only)
            payload = jwt.get_unverified_claims(id_token)
            
            logger.warning(
                "ID token decoded without verification - NOT SECURE FOR PRODUCTION!"
            )
            
            return payload
        
        except Exception as e:
            logger.error(f"Error decoding ID token: {e}")
            return None


# Global instance
google_oauth_client = GoogleOAuthClient()
