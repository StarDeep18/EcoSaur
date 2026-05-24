from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TINYDB_PATH: str = "ecosaur_db.json"
    GEMINI_API_KEY: str = "placeholder_gemini_key"

    class Config:
        env_file = ".env"

settings = Settings()
