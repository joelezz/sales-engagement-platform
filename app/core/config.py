from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    app_name: str = "Sales Engagement Platform"
    debug: bool = False
    version: str = "1.0.0"
    environment: str = "development"
    
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost/sales_engagement"
    database_pool_size: int = 20
    database_max_overflow: int = 30
    
    # Legacy database environment variables (for compatibility)
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_db: Optional[str] = None
    postgres_host: Optional[str] = None
    postgres_port: Optional[str] = None
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production-min-32-chars"
    jwt_secret_key: Optional[str] = None  # Alternative JWT key
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours for production
    refresh_token_expire_days: int = 7
    
    # Twilio
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    twilio_webhook_url: Optional[str] = None
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8001"
    allowed_origins: Optional[str] = None  # Alternative CORS setting
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        origins = self.allowed_origins or self.cors_origins
        return [origin.strip() for origin in origins.split(",") if origin.strip()]
    
    @property
    def effective_database_url(self) -> str:
        """Get database URL, constructing from parts if needed"""
        if self.database_url and not self.database_url.startswith("postgresql+asyncpg://user:password"):
            return self.database_url
        
        # Construct from individual parts if available
        if all([self.postgres_user, self.postgres_password, self.postgres_db, self.postgres_host]):
            port = self.postgres_port or "5432"
            return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{port}/{self.postgres_db}"
        
        return self.database_url
    
    @property
    def effective_jwt_secret(self) -> str:
        """Get JWT secret key, preferring jwt_secret_key over secret_key"""
        return self.jwt_secret_key or self.secret_key
    
    # Base URL for webhooks
    base_url: str = "https://your-domain.com"
    
    # Celery
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    
    @property
    def effective_celery_broker(self) -> str:
        """Get Celery broker URL, defaulting to Redis"""
        if self.celery_broker_url:
            return self.celery_broker_url
        # Use Redis URL with different DB
        if self.redis_url:
            return self.redis_url.replace("/0", "/1")
        return "redis://localhost:6379/1"
    
    @property
    def effective_celery_backend(self) -> str:
        """Get Celery result backend URL, defaulting to Redis"""
        if self.celery_result_backend:
            return self.celery_result_backend
        # Use Redis URL with different DB
        if self.redis_url:
            return self.redis_url.replace("/0", "/2")
        return "redis://localhost:6379/2"
    
    # Monitoring
    prometheus_enabled: bool = True
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Allow extra fields for flexibility
        extra = "ignore"


settings = Settings()