from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.agents.base_agent import BaseAgent
from src.services.transcription_service import TranscriptionResult, TranscriptionService
from src.utils.error_handlers import handle_connection_errors

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    run_topic: bool = True
    run_decision: bool = True
    run_action: bool = True
    run_sentiment: bool = True
    run_summary: bool = True


class AgentOrchestrator:
    """
    Orchestrator that runs transcription then agents sequentially.
    
    Handles connection errors and timeouts gracefully:
    - Retries failed agent runs with exponential backoff
    - Timeouts prevent hanging operations
    - Partial failures are captured without stopping the pipeline
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
        Process meeting with granular progress updates and error handling.
        
        Args:
            meeting_id: Unique identifier for the meeting
            audio_path: Path to audio file
            on_status: Callback for status updates (status, progress, stage_description)
            
        Returns:
            Dictionary with transcript and agent results
        """
        # Transcribe (handled by transcription_service with its own progress)
        try:
            transcript: TranscriptionResult = self.transcription_service.transcribe(
                audio_path, 
                meeting_id=meeting_id,
                on_status=on_status
            )
        except Exception as e:
            logger.error(f"[AgentOrchestrator] Transcription failed: {e}")
            raise

        payload: Dict[str, Any] = {
            "text": transcript.text,
            "segments": [asdict(seg) for seg in transcript.segments],
            "meeting_id": meeting_id,
        }

        results: Dict[str, Any] = {"transcript": asdict(transcript)}

        # Run agents with granular progress tracking and error resilience
        total_agents = len(self.agents)
        base_progress = 80  # Start after transcription (which goes to ~75%)
        progress_per_agent = 15 / total_agents if total_agents > 0 else 0  # 15% for all agents (80-95%)

        async def run_agent_with_retry(
            agent: BaseAgent, 
            index: int,
            max_retries: int = 2
        ) -> Dict[str, Any]:
            """Run agent with retry logic and connection error handling."""
            agent_name = agent.name.replace("_", " ").title()
            delay = 1.0
            
            for attempt in range(max_retries + 1):
                try:
                    # Update status before running agent
                    agent_progress = base_progress + (index * progress_per_agent)
                    if on_status:
                        on_status(
                            "generating_insights",
                            agent_progress,
                            f"Running {agent_name} agent"
                        )
                        logger.info(
                            f"[AgentOrchestrator] Running {agent_name} "
                            f"(attempt {attempt + 1}/{max_retries + 1}, progress: {agent_progress:.1f}%)"
                        )
                    
                    # Run agent with timeout (60 seconds per agent)
                    try:
                        result = await asyncio.wait_for(
                            agent.run(payload),
                            timeout=60
                        )
                    except asyncio.TimeoutError:
                        logger.warning(f"[AgentOrchestrator] {agent_name} timed out (60s)")
                        if attempt < max_retries:
                            await asyncio.sleep(delay)
                            delay *= 2  # Exponential backoff
                            continue
                        else:
                            logger.error(f"[AgentOrchestrator] {agent_name} timeout after {max_retries + 1} attempts")
                            return {agent.name: "error: operation timed out"}
                    except (ConnectionResetError, ConnectionAbortedError, ConnectionRefusedError, BrokenPipeError) as e:
                        logger.warning(
                            f"[AgentOrchestrator] {agent_name} connection error on attempt {attempt + 1}: {e}"
                        )
                        if attempt < max_retries:
                            await asyncio.sleep(delay)
                            delay *= 2  # Exponential backoff
                            continue
                        else:
                            logger.error(f"[AgentOrchestrator] {agent_name} connection failed after {max_retries + 1} attempts")
                            return {agent.name: "error: connection to agent failed"}
                    
                    # Update status after completing agent
                    completed_progress = base_progress + ((index + 1) * progress_per_agent)
                    if on_status:
                        on_status(
                            "generating_insights",
                            completed_progress,
                            f"Completed {agent_name} agent"
                        )
                        logger.info(
                            f"[AgentOrchestrator] Completed {agent_name} "
                            f"(progress: {completed_progress:.1f}%)"
                        )
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"[AgentOrchestrator] {agent_name} non-recoverable error: {e}")
                    return {agent.name: f"error: {type(e).__name__}: {str(e)[:100]}"}
            
            # Should not reach here
            return {agent.name: "error: max retries exceeded"}

        # Run agents sequentially to show progress for each one
        for idx, agent in enumerate(self.agents):
            agent_result = await run_agent_with_retry(agent, idx)
            results.update(agent_result)

        return results
