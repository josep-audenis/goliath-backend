"""Runtime settings. Env-driven; safe defaults so the app boots with no secrets."""

from __future__ import annotations

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "goliath-backend"
    env: str = "dev"
    debug: bool = False

    # ---- LLM (OpenAI-compatible; Groq by default, OpenAI or HF optional) ----
    llm_provider: str = "groq"  # "groq" | "openai" | "hf"
    agent_model: str = "llama-3.3-70b-versatile"

    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"

    openai_api_key: str = Field(default="", validation_alias=AliasChoices("openai_api_key", "OPENAI_API_KEY"))
    openai_base_url: str = "https://api.openai.com/v1"

    hf_token: str = Field(default="", validation_alias=AliasChoices("hf_token", "HF_TOKEN"))
    hf_space_base_url: str = ""
    hf_model: str = "Qwen/Qwen2.5-32B-Instruct"

    # ---- Cala ----
    # REST layer for structured entity/knowledge lookups.
    cala_base_url: str = "https://api.cala.ai/v1"
    cala_api_key: str = ""
    # MCP layer for open-ended knowledge_search inside agents.
    cala_mcp_url: str = "https://api.cala.ai/mcp/"
    cala_mcp_api_key: str = ""
    use_cala_mock: bool = True  # when true, subagents return credible mock data

    # ---- ElevenLabs (backend-side TTS; keys never reach frontend) ----
    elevenlabs_api_key: str = ""
    elevenlabs_base_url: str = "https://api.elevenlabs.io/v1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def _infer_provider(self) -> "Settings":
        # If only one key is set, prefer that provider.
        if not self.groq_api_key and self.openai_api_key and self.llm_provider == "groq":
            self.llm_provider = "openai"
        if not self.groq_api_key and not self.openai_api_key and self.hf_token:
            self.llm_provider = "hf"
        return self

    @property
    def has_llm_key(self) -> bool:
        return bool(
            {"groq": self.groq_api_key, "openai": self.openai_api_key, "hf": self.hf_token}.get(
                self.llm_provider
            )
        )

    @property
    def cala_live(self) -> bool:
        """Real Cala calls only when a key exists and mock is off."""
        return bool(self.cala_api_key) and not self.use_cala_mock


settings = Settings()
