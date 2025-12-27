"""End-to-end pipeline tests."""

import io
import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from src.main import app
from src.services.transcription_service import TranscriptionService, TranscriptionResult, TranscriptionSegment
from src.services.agent_orchestrator import AgentOrchestrator
from src.agents.topic_agent import TopicAgent
from src.agents.decision_agent import DecisionAgent
from src.agents.action_item_agent import ActionItemAgent
from src.agents.sentiment_agent import SentimentAgent
from src.agents.summary_agent import SummaryAgent


@pytest.fixture
def mock_transcription_result():
    """Create a mock transcription result."""
    return TranscriptionResult(
        text="Welcome to the meeting. We decided to proceed with the project. John will send the proposal by Friday.",
        segments=[
            TranscriptionSegment(text="Welcome to the meeting.", start=0.0, end=2.0, speaker="SPEAKER_00"),
            TranscriptionSegment(text="We decided to proceed with the project.", start=2.0, end=5.0, speaker="SPEAKER_01"),
            TranscriptionSegment(text="John will send the proposal by Friday.", start=5.0, end=8.0, speaker="SPEAKER_00"),
        ],
        model="test_model"
    )


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_pipeline_flow(mock_transcription_result, temp_storage_dir):
    """Test the complete pipeline from transcription to insights."""
    # Mock transcription service
    transcription_service = MagicMock(spec=TranscriptionService)
    transcription_service.transcribe = MagicMock(return_value=mock_transcription_result)
    
    # Create agents with mocked LLM calls
    agents = [
        TopicAgent(token="test_token"),
        DecisionAgent(),
        ActionItemAgent(),
        SentimentAgent(),
        SummaryAgent(token="test_token")
    ]
    
    # Mock LLM calls for agents that need them
    with patch('src.agents.topic_agent.get_mistral_completion', new_callable=AsyncMock) as mock_topic_llm:
        with patch('src.agents.summary_agent.get_mistral_completion', new_callable=AsyncMock) as mock_summary_llm:
            mock_topic_llm.return_value = '[{"topic": "Project Discussion", "keywords": ["project"], "summary": "Discussion about project"}]'
            mock_summary_llm.side_effect = ["Test paragraph summary", "- Test bullet 1\n- Test bullet 2"]
            
            # Create orchestrator
            orchestrator = AgentOrchestrator(
                transcription_service=transcription_service,
                agents=agents
            )
            
            # Create a dummy audio file path
            audio_path = temp_storage_dir / "test_audio.wav"
            audio_path.touch()
            
            # Track status updates
            status_updates = []
            def on_status(status, progress, description):
                status_updates.append((status, progress, description))
            
            # Run pipeline
            result = await orchestrator.process(
                meeting_id="test_meeting_e2e",
                audio_path=audio_path,
                on_status=on_status
            )
            
            # Verify results
            assert "transcript" in result
            assert "topic_agent" in result or "topics" in result
            assert "decision_agent" in result or "decisions" in result
            assert "action_item_agent" in result or "action_items" in result
            assert "sentiment_agent" in result or "sentiment" in result
            assert "summary_agent" in result or "summary" in result
            
            # Verify status updates were called
            assert len(status_updates) > 0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_pipeline_error_handling(temp_storage_dir):
    """Test pipeline error handling."""
    # Mock transcription service that fails
    transcription_service = MagicMock(spec=TranscriptionService)
    transcription_service.transcribe = MagicMock(side_effect=Exception("Transcription failed"))
    
    agents = [TopicAgent(token="test_token")]
    
    orchestrator = AgentOrchestrator(
        transcription_service=transcription_service,
        agents=agents
    )
    
    audio_path = temp_storage_dir / "test_audio.wav"
    audio_path.touch()
    
    # Should raise exception
    with pytest.raises(Exception):
        await orchestrator.process(
            meeting_id="test_meeting_error",
            audio_path=audio_path
        )


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_pipeline_agent_timeout(temp_storage_dir, mock_transcription_result):
    """Test pipeline handles agent timeouts gracefully."""
    transcription_service = MagicMock(spec=TranscriptionService)
    transcription_service.transcribe = MagicMock(return_value=mock_transcription_result)
    
    # Create an agent that times out
    slow_agent = MagicMock()
    slow_agent.name = "slow_agent"
    slow_agent.run = AsyncMock(side_effect=asyncio.TimeoutError())
    
    agents = [slow_agent]
    
    orchestrator = AgentOrchestrator(
        transcription_service=transcription_service,
        agents=agents
    )
    
    audio_path = temp_storage_dir / "test_audio.wav"
    audio_path.touch()
    
    # Should handle timeout gracefully
    result = await orchestrator.process(
        meeting_id="test_meeting_timeout",
        audio_path=audio_path
    )
    
    # Should still return results (with error for timed out agent)
    assert "transcript" in result
    assert "slow_agent" in result

