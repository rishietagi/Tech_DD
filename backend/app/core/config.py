from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./techdd.db"
    cors_origins: str = "http://localhost:3000"
    scope_generator: Literal["placeholder", "rules", "llm"] = "rules"
    api_version: str = "0.2.0"

    # LLM tailoring (Phase 2). An absent key is not an error: the factory falls back
    # to the deterministic RulesScopeGenerator with a logged warning.
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-opus-5"
    llm_max_tokens: int = 16000

    @property
    def llm_enabled(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
