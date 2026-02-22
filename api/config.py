import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM
    openrouter_api_key: str = ""
    llm_model: str = "anthropic/claude-3.5-sonnet"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 4096
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Database (Render provides DATABASE_URL)
    postgres_url: str = ""

    @property
    def database_url(self) -> str:
        # Use DATABASE_URL from Render, or postgres_url, or default
        return os.environ.get("DATABASE_URL") or self.postgres_url

    # Vector DB - Qdrant Cloud
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "agent_documents"

    # Observability - LangWatch
    langwatch_api_key: str = ""

    # Auth
    app_secret: str = "change-me"
    admin_password: str = "admin123"

    # Storage
    upload_dir: str = "/app/uploads"
    agents_dir: str = "/app/agents"
    chunk_size: int = 512
    chunk_overlap: int = 50

    # App
    debug: bool = False

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
