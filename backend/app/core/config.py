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
    #
    # NOTE: CLAUDE.md §3 specifies the Anthropic API. Rishi chose Gemini on 2026-08-30
    # because it has a free tier and a Claude Pro subscription does not include API
    # credits. Recorded here so the code and the constitution do not silently disagree.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    llm_max_tokens: int = 16000
    llm_temperature: float = 0.2

    # The intelligence pipeline (Phase 7, Rishi 2026-11-18). One switch for every
    # generator: "off" runs the deterministic rules everywhere even when a key is present;
    # "auto" turns the LLM on for every skill whose key is configured. Ships "off".
    # SCOPE_GENERATOR no longer selects rules vs LLM — it only still honours "placeholder".
    ai_mode: Literal["off", "auto"] = "off"
    # Comma-separated skill names to keep deterministic even under "auto".
    ai_disabled_skills: str = ""

    # Where the client drops documents. A relative path resolves against the repo root
    # (the backend runs from `backend/`), which is what makes the local fixture work
    # unchanged; at deployment this is an absolute path to the real share.
    shared_drive_root: str = "../shared-drive/project-kiln"

    @property
    def llm_key_present(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def llm_enabled(self) -> bool:
        """True only when the mode allows it AND a key is configured."""
        return self.ai_mode == "auto" and self.llm_key_present

    @property
    def disabled_skills(self) -> set[str]:
        return {s.strip() for s in self.ai_disabled_skills.split(",") if s.strip()}

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
