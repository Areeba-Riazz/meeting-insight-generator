from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    llm_model: str = "mistralai/Mistral-7B-Instruct-v0.2"
    temperature: float = 0.2
    max_tokens: int = 1024
    use_local_llm: bool = True
    device: str = "cpu"
    timeout: int = 30
    max_retries: int = 2
    model_type: str = "mistral"  # options: mistral, llama, mock
    mistral_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  # tolerate unrelated env vars
    )

