from __future__ import annotations

from typing import Any, Dict, Optional

from backend.src.agents.config import AgentSettings


class LLMClient:
    """
    LangChain-backed LLM client with graceful fallback to mock responses
    when no model/key is available.
    """

    def __init__(self, settings: AgentSettings | None = None) -> None:
        self.settings = settings or AgentSettings()
        self._llm = None

    def _load_llm(self):
        if self._llm is not None:
            return self._llm

        if self.settings.model_type == "mistral":
            try:
                from langchain_community.chat_models import ChatMistralAI

                self._llm = ChatMistralAI(
                    model=self.settings.llm_model,
                    temperature=self.settings.temperature,
                    max_tokens=self.settings.max_tokens,
                    timeout=self.settings.timeout,
                )
                return self._llm
            except Exception:
                pass

        # Fallback to mock
        self._llm = None
        return None

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        llm = self._load_llm()
        if llm is None:
            return f"[LLM mock] {prompt[:200]}..."

        try:
            # LangChain chat models expect messages; use a simple system/user pattern
            from langchain.schema import HumanMessage

            resp = await llm.apredict_messages([HumanMessage(content=prompt)])
            return resp.content
        except Exception:
            return f"[LLM error fallback] {prompt[:200]}..."

