from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TINYDB_PATH: str = "ecosaur_db.json"
    GEMINI_API_KEY: str = "AIzaSyDc9XCvB9qITbSvnTY1Gt2Tq7SJKOwwMZU"

    class Config:
        env_file = ".env"

settings = Settings()
