from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = "AIzaSyCn07OG9N1_DWZZDHzvWdAW6LyrzAWcN0Y"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
