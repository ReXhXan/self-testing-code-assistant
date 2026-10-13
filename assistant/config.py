"""Central configuration, loaded from environment variables / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "mock"
    llm_model: str = "llama3.1"
    llm_temperature: float = 0.2
    openai_api_key: str = ""
    groq_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    max_iterations: int = 4
    sandbox_timeout_s: float = 20.0
    sandbox_memory_mb: int = 512
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
