from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    # OpenAI (optional, currently unused)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    # Gemini configuration
    google_api_key: Optional[str] = None
    google_model: str = "gemini-2.0-flash"
    
    # CORS
    allow_origins: str = "http://localhost:5173"

    class Config:
        env_file = str(Path(__file__).resolve().parents[1] / ".env")

settings = Settings()