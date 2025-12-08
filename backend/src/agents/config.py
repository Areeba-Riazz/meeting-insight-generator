from __future__ import annotations

from pydantic import BaseSettings


class AgentSettings(BaseSettings):
    llm_model: str = "mistralai/Mistral-7B-Instruct-v0.2"
    temperature: float = 0.2
    max_tokens: int = 1024
    use_local_llm: bool = True
    device: str = "cpu"
    timeout: int = 30
    max_retries: int = 2
    model_type: str = "mistral"  # options: mistral, llama, mock

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

