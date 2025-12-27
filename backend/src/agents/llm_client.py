from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Optional

from src.agents.config import AgentSettings
from src.utils.cache import cached_llm_call
from src.utils.error_handlers import handle_connection_errors

logger = logging.getLogger(__name__)


@cached_llm_call
@handle_connection_errors(max_retries=2, timeout=30)
async def get_mistral_completion(
    prompt: str,
    max_tokens: int = 500,
    temperature: float = 0.3,
    api_key: Optional[str] = None
) -> str:
    """
    Get Mistral AI completions with automatic retry on connection errors.
    Uses the Mistral API directly for better control.
    
    Handles:
    - Connection reset/refused errors
    - Timeout errors
    - Automatic retry with exponential backoff
    
    Falls back gracefully if all retries fail.
    """
    api_key = api_key or os.getenv("MISTRAL_API_KEY")
    
    if not api_key:
        logger.warning("[LLMClient] No MISTRAL_API_KEY found, using fallback")
        return "AI analysis unavailable - please configure MISTRAL_API_KEY"
    
    try:
        from mistralai import Mistral
        
        client = Mistral(api_key=api_key)
        
        # Mistral API call with timeout handling
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.chat.complete,
                model="mistral-small-latest",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            ),
            timeout=30
        )
        
        if response and response.choices:
            return response.choices[0].message.content
        
        logger.warning("[LLMClient] Empty response from Mistral API")
        return "No response from AI"
        
    except asyncio.TimeoutError as e:
        logger.error(f"[LLMClient] Mistral API timeout: {e}")
        return "AI analysis timed out - please try again"
    except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError) as e:
        logger.error(f"[LLMClient] Mistral API connection error: {e}")
        return "Connection to AI service lost - please try again"
    except Exception as e:
        logger.error(f"[LLMClient] Mistral API error: {e}")
        return f"Error generating AI insights: {str(e)}"


class LLMClient:
    """
    LangChain-backed LLM client with graceful fallback to mock responses
    when no model/key is available.
    
    Handles connection errors and timeouts gracefully.
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
            except Exception as e:
                logger.warning(f"[LLMClient] Failed to load ChatMistralAI: {e}")
                pass

        # Fallback to mock
        self._llm = None
        return None

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate text using LLM with connection error handling.
        
        Gracefully falls back to mock response on connection errors.
        """
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

            try:
                resp = await asyncio.wait_for(
                    llm.apredict_messages(messages),
                    timeout=self.settings.timeout or 30
                )
                return resp.content
            except asyncio.TimeoutError:
                logger.warning("[LLMClient] LLM prediction timeout")
                return f"[LLM timeout fallback] {prompt[:200]}..."
            except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError) as e:
                logger.warning(f"[LLMClient] Connection error: {e}")
                return f"[LLM connection error fallback] {prompt[:200]}..."
                
        except Exception as e:
            logger.error(f"[LLMClient] Unexpected error: {e}")
            return f"[LLM error fallback] {prompt[:200]}..."
