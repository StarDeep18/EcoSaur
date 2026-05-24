from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TINYDB_PATH: str = "ecosaur_db.json"
    GEMINI_API_KEY: str = "AIzaSyCn07OG9N1_DWZZDHzvWdAW6LyrzAWcN0Y"

    class Config:
        env_file = ".env"

settings = Settings()
