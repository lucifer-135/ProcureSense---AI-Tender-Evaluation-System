from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/tender_eval"
    REDIS_URL: str = "redis://localhost:6379/0"
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
