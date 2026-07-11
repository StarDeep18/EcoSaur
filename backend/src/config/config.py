from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys & DB Config with default placeholders to allow local runs / testing
    GEMINI_API_KEY: str = "placeholder_gemini_key"
    SUPABASE_URL: str = "http://localhost:54321"
    SUPABASE_ANON_KEY: str = "placeholder_anon_key"
    SUPABASE_JWT_SECRET: str = "placeholder_jwt_secret"
    DATABASE_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
