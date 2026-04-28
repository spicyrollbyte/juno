"""Simplified configuration management."""

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


def _load_env_file() -> None:
    """Load .env from root directory if present."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.is_file():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key, value = stripped.split("=", 1)
                key, value = key.strip(), value.strip().strip("'\"")
                if key and value and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        pass


_load_env_file()


DEFAULT_APP_NAME = "Juno Server"
DEFAULT_APP_VERSION = "0.3.0"


def _env_int(name: str, fallback: int) -> int:
    try:
        return int(os.getenv(name, str(fallback)))
    except (TypeError, ValueError):
        return fallback


class Settings(BaseModel):
    """Application settings with lightweight env fallbacks."""

    # App metadata
    app_name: str = Field(default=DEFAULT_APP_NAME)
    app_version: str = Field(default=DEFAULT_APP_VERSION)

    # Server runtime
    server_host: str = Field(default=os.getenv("JUNO_HOST", "0.0.0.0"))
    server_port: int = Field(default=_env_int("JUNO_PORT", 8001))

    # LLM provider (any OpenAI-compatible endpoint)
    llm_base_url: str = Field(default=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"))
    llm_api_key: Optional[str] = Field(default=os.getenv("LLM_API_KEY"))

    # LLM model selection (overridable per-role)
    interaction_agent_model: str = Field(default=os.getenv("LLM_MODEL", "claude-sonnet-4-6"))
    execution_agent_model: str = Field(default=os.getenv("EXECUTION_MODEL", "claude-haiku-4-5-20251001"))
    execution_agent_search_model: str = Field(default=os.getenv("EXECUTION_MODEL", "claude-haiku-4-5-20251001"))
    summarizer_model: str = Field(default=os.getenv("EXECUTION_MODEL", "claude-haiku-4-5-20251001"))
    email_classifier_model: str = Field(default=os.getenv("LLM_MODEL", "claude-sonnet-4-6"))

    # Twilio (SMS)
    twilio_account_sid: Optional[str] = Field(default=os.getenv("TWILIO_ACCOUNT_SID"))
    twilio_auth_token: Optional[str] = Field(default=os.getenv("TWILIO_AUTH_TOKEN"))
    twilio_phone_number: Optional[str] = Field(default=os.getenv("TWILIO_PHONE_NUMBER"))

    # Credentials / integrations
    # Kept for backward compat — prefer LLM_API_KEY
    anthropic_api_key: Optional[str] = Field(default=os.getenv("ANTHROPIC_API_KEY"))
    composio_gmail_auth_config_id: Optional[str] = Field(default=os.getenv("COMPOSIO_GMAIL_AUTH_CONFIG_ID"))
    composio_gcal_auth_config_id: Optional[str] = Field(default=os.getenv("COMPOSIO_GCAL_AUTH_CONFIG_ID"))
    composio_sheets_auth_config_id: Optional[str] = Field(default=os.getenv("COMPOSIO_SHEETS_AUTH_CONFIG_ID"))
    composio_api_key: Optional[str] = Field(default=os.getenv("COMPOSIO_API_KEY"))

    # HTTP behaviour
    cors_allow_origins_raw: str = Field(default=os.getenv("JUNO_CORS_ALLOW_ORIGINS", "*"))
    enable_docs: bool = Field(default=os.getenv("JUNO_ENABLE_DOCS", "1") != "0")
    docs_url: Optional[str] = Field(default=os.getenv("JUNO_DOCS_URL", "/docs"))

    # Summarisation controls
    conversation_summary_threshold: int = Field(default=10)
    conversation_summary_tail_size: int = Field(default=4)

    @property
    def resolved_api_key(self) -> Optional[str]:
        """LLM_API_KEY, falling back to ANTHROPIC_API_KEY for backward compat."""
        return self.llm_api_key or self.anthropic_api_key

    @property
    def cors_allow_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_allow_origins_raw.strip() in {"", "*"}:
            return ["*"]
        return [origin.strip() for origin in self.cors_allow_origins_raw.split(",") if origin.strip()]

    @property
    def resolved_docs_url(self) -> Optional[str]:
        """Return documentation URL when docs are enabled."""
        return (self.docs_url or "/docs") if self.enable_docs else None

    @property
    def summarization_enabled(self) -> bool:
        """Flag indicating conversation summarisation is active."""
        return self.conversation_summary_threshold > 0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
