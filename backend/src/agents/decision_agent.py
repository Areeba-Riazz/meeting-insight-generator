from __future__ import annotations

from typing import Any, Dict, List

from .base_agent import BaseAgent
from .config import AgentSettings
from .llm_client import LLMClient


class DecisionAgent(BaseAgent):
    name = "decision_agent"

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient(AgentSettings())

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        transcript_segments: List[Dict[str, Any]] = payload.get("segments", [])
        text = payload.get("text", "")
        prompt = (
            "Extract decisions from the meeting transcript. "
            "For each decision, include: decision statement, participants/approvers, "
            "and a short rationale. Return concise bullet-style text.\n\n"
            f"Transcript:\n{text}\n"
        )
        llm_resp = await self.llm.generate(prompt)
        decisions = [
            {
                "decision": llm_resp[:160],
                "participants": [],
                "evidence": seg.get("text", ""),
                "start": seg.get("start"),
                "end": seg.get("end"),
            }
            for seg in transcript_segments
        ]
        return {"decisions": decisions}

