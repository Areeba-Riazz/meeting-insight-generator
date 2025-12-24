from __future__ import annotations

import os
from typing import Any, Dict, Optional

from src.agents.config import AgentSettings


async def get_mistral_completion(
    prompt: str,
    max_tokens: int = 500,
    temperature: float = 0.3,
    api_key: Optional[str] = None
) -> str:
    """
    Simple helper function to get Mistral AI completions.
    Uses the Mistral API directly for better control.
    """
    api_key = api_key or os.getenv("MISTRAL_API_KEY")
    
    if not api_key:
        print("[LLMClient] No MISTRAL_API_KEY found, using fallback")
        # Return a simple fallback
        return "AI analysis unavailable - please configure MISTRAL_API_KEY"
    
    try:
        from mistralai import Mistral
        
        client = Mistral(api_key=api_key)
        
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if response and response.choices:
            return response.choices[0].message.content
        
        return "No response from AI"
        
    except Exception as e:
        print(f"[LLMClient] Mistral API error: {e}")
        return f"Error generating AI insights: {str(e)}"


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
                    api_key=self.settings.mistral_api_key,
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
            from langchain.schema import HumanMessage, SystemMessage

            system_prompt = kwargs.get("system_prompt")
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))

            resp = await llm.apredict_messages(messages)
            return resp.content
        except Exception:
            return f"[LLM error fallback] {prompt[:200]}..."

