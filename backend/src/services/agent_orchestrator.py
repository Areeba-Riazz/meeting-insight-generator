from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from src.agents.base_agent import BaseAgent
from src.services.transcription_service import TranscriptionResult, TranscriptionService


@dataclass
class OrchestratorConfig:
    run_topic: bool = True
    run_decision: bool = True
    run_action: bool = True
    run_sentiment: bool = True
    run_summary: bool = True


class AgentOrchestrator:
    """
    Simple orchestrator that runs transcription then agents sequentially.
    Parallelism can be added later if needed.
    """

    def __init__(
        self,
        transcription_service: TranscriptionService,
        agents: List[BaseAgent],
        config: OrchestratorConfig | None = None,
    ) -> None:
        self.transcription_service = transcription_service
        self.agents = agents
        self.config = config or OrchestratorConfig()

    async def process(self, meeting_id: str, audio_path: Path) -> Dict[str, Any]:
        # Transcribe
        transcript: TranscriptionResult = self.transcription_service.transcribe(audio_path, meeting_id=meeting_id)

        payload: Dict[str, Any] = {
            "text": transcript.text,
            "segments": [seg.__dict__ for seg in transcript.segments],
            "meeting_id": meeting_id,
        }

        results: Dict[str, Any] = {"transcript": transcript.__dict__}

        async def run_agent(agent: BaseAgent):
            try:
                return await asyncio.wait_for(agent.run(payload), timeout=60)
            except Exception as e:
                return {agent.name: f"error: {e}"}

        agent_tasks = [run_agent(agent) for agent in self.agents]
        agent_results = await asyncio.gather(*agent_tasks)
        for res in agent_results:
            results.update(res)

        return results

