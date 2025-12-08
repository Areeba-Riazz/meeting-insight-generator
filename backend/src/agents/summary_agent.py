from __future__ import annotations

from typing import Any, Dict

from .base_agent import BaseAgent
from .config import AgentSettings
from .llm_client import LLMClient


class SummaryAgent(BaseAgent):
    name = "summary_agent"

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient(AgentSettings())

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text: str = payload.get("text", "")
        prompt = (
            "Provide a concise meeting summary (bullets). Include key decisions and action items "
            "if present. Keep it under 120 words.\n\n"
            f"Transcript:\n{text}\n"
        )
        summary = await self.llm.generate(prompt)
        return {"summary": summary}

