from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_api_key: str | None = None
    google_model: str = "gemini-2.0-flash"

    max_candidates_for_llm: int = 25
    max_evidence_items: int = 12

    pipeline_version: str = "skills-v1"
    prompt_version: str = "professional-v1"

    allow_origins: str = "*"

    class Config:
        env_file = str(Path(__file__).resolve().parents[1] / ".env")


settings = Settings()
