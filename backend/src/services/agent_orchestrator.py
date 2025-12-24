from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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

    async def process(
        self, 
        meeting_id: str, 
        audio_path: Path,
        on_status: Optional[Callable[[str, Optional[float], Optional[str]], None]] = None
    ) -> Dict[str, Any]:
        """
        Process meeting with granular progress updates.
        
        Args:
            meeting_id: Unique identifier for the meeting
            audio_path: Path to audio file
            on_status: Callback for status updates (status, progress, stage_description)
        """
        # Transcribe (handled by transcription_service with its own progress)
        transcript: TranscriptionResult = self.transcription_service.transcribe(
            audio_path, 
            meeting_id=meeting_id,
            on_status=on_status
        )

        payload: Dict[str, Any] = {
            "text": transcript.text,
            "segments": [seg.__dict__ for seg in transcript.segments],
            "meeting_id": meeting_id,
        }

        results: Dict[str, Any] = {"transcript": transcript.__dict__}

        # Run agents with granular progress tracking
        total_agents = len(self.agents)
        base_progress = 80  # Start after transcription (which goes to ~75%)
        progress_per_agent = 15 / total_agents if total_agents > 0 else 0  # 15% for all agents (80-95%)

        async def run_agent(agent: BaseAgent, index: int):
            try:
                # Update status before running agent
                agent_progress = base_progress + (index * progress_per_agent)
                agent_name = agent.name.replace("_", " ").title()
                if on_status:
                    on_status(
                        "generating_insights",
                        agent_progress,
                        f"Running {agent_name} agent"
                    )
                    print(f"[AgentOrchestrator] Running {agent_name} (progress: {agent_progress:.1f}%)")
                
                result = await asyncio.wait_for(agent.run(payload), timeout=60)
                
                # Update status after completing agent
                completed_progress = base_progress + ((index + 1) * progress_per_agent)
                if on_status:
                    on_status(
                        "generating_insights",
                        completed_progress,
                        f"Completed {agent_name} agent"
                    )
                    print(f"[AgentOrchestrator] Completed {agent_name} (progress: {completed_progress:.1f}%)")
                
                return result
            except Exception as e:
                print(f"[AgentOrchestrator] Error running {agent.name}: {e}")
                return {agent.name: f"error: {e}"}

        # Run agents sequentially to show progress for each one
        for idx, agent in enumerate(self.agents):
            agent_result = await run_agent(agent, idx)
            results.update(agent_result)

        return results

