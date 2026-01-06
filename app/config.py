"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # PostgreSQL
    DATABASE_URL: str
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_USER: int = 900  # 15 minutes
    JWT_ACCESS_TOKEN_EXPIRE_SYSTEM: int = 3600  # 1 hour
    
    # System Accounts Secret Keys
    SYSTEM_1_SECRET: str
    SYSTEM_2_SECRET: str
    SYSTEM_3_SECRET: str
    SYSTEM_4_SECRET: str
    SYSTEM_5_SECRET: str
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_TOPIC_NEW_USERS: str = "new_users"
    
    # Application
    APP_PORT: int = 8012
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    def get_system_secret(self, username: str) -> str | None:
        """Get system account secret by username."""
        system_secrets = {
            "system_1": self.SYSTEM_1_SECRET,
            "system_2": self.SYSTEM_2_SECRET,
            "system_3": self.SYSTEM_3_SECRET,
            "system_4": self.SYSTEM_4_SECRET,
            "system_5": self.SYSTEM_5_SECRET,
        }
        return system_secrets.get(username)


settings = Settings()
