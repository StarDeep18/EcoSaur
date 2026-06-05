from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = "placeholder_gemini_key"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
