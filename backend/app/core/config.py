from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://cogniverve:password@localhost:5432/cogniverve_db"
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # LLM Providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    litellm_log: str = "INFO"
    
    # Search
    tavily_api_key: Optional[str] = None
    
    # Email
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Environment
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # File Storage
    upload_dir: str = "./uploads"
    max_file_size: int = 10485760  # 10MB
    
    # Agent Settings
    default_model: str = "gpt-4"
    default_temperature: float = 0.7
    max_execution_time: int = 3600  # 1 hour
    max_retry_attempts: int = 3
    
    # Vector Database
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    
    # Monitoring
    prometheus_port: int = 9090
    enable_metrics: bool = True
    
    # Stripe Payment Processing
    stripe_publishable_key: str = "pk_test_your_key_here"
    stripe_secret_key: str = "sk_test_your_key_here"
    stripe_webhook_secret: str = "whsec_your_secret_here"
    frontend_url: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

