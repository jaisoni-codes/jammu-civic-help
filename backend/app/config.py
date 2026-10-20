import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bharosa Jammu"
    ENV: str = "development"
    DEBUG: bool = True
    
    # Database: Supports SQLite (offline standalone) or PostgreSQL with PostGIS
    DATABASE_URL: str = "sqlite:///./bharosa.db"
    
    # Simulated Clock
    DEMO_OFFSET_HOURS: float = 0.0
    
    # AI Mode
    MOCK_AI: bool = True
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBED_MODEL: str = "text-embedding-004"
    
    # Channel selection: console | telegram | whatsapp
    CHANNEL: str = "console"
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    
    # WhatsApp Cloud API
    WHATSAPP_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: str = "bharosa_secret_token_2026"
    
    # JWT Auth for Officers/Admins
    JWT_SECRET: str = "bharosa_jammu_jwt_secret_key_change_in_prod_7788"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 60 * 24 * 7  # 7 days for hackathon ease
    
    # Base URL for public links (in SMS / WhatsApp / Simulator)
    BASE_URL: str = "http://localhost:3000"
    API_BASE_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
