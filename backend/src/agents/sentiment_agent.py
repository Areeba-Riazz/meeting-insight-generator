from __future__ import annotations

from typing import Any, Dict, List

from .base_agent import BaseAgent
from .config import AgentSettings
from .llm_client import LLMClient


class SentimentAgent(BaseAgent):
    name = "sentiment_agent"

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient(AgentSettings())

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        transcript_segments: List[Dict[str, Any]] = payload.get("segments", [])
        # Per-segment sentiment classification via LLM
        sentiments = []
        for seg in transcript_segments:
            prompt = (
                "Classify the sentiment of this meeting segment as one of "
                "[positive, neutral, negative] and give a short rationale.\n\n"
                f"Segment:\n{seg.get('text', '')}\n"
            )
            sentiment = await self.llm.generate(prompt)
            sentiments.append(
                {
                    "sentiment": sentiment[:120],
                    "start": seg.get("start"),
                    "end": seg.get("end"),
                    "text": seg.get("text", ""),
                }
            )
        return {"sentiments": sentiments}

