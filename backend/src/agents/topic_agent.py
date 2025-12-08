from __future__ import annotations

from typing import Any, Dict, List

from .base_agent import BaseAgent
from .llm_client import LLMClient
from .config import AgentSettings


class TopicAgent(BaseAgent):
    name = "topic_agent"

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient(AgentSettings())

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        transcript_segments: List[Dict[str, Any]] = payload.get("segments", [])
        text = payload.get("text", "")
        prompt = (
            "You are a meeting analysis assistant. Identify key topic segments "
            "from the meeting transcript. Return a concise list of topic labels, "
            "each with start/end seconds and the key sentence.\n\n"
            f"Transcript:\n{text}\n"
        )
        llm_resp = await self.llm.generate(prompt)
        topics = [
            {
                "topic": llm_resp[:120],
                "start": seg.get("start"),
                "end": seg.get("end"),
                "text": seg.get("text", ""),
            }
            for seg in transcript_segments
        ]
        return {"topics": topics}

