"""Performance tests."""

import time
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from src.agents.topic_agent import TopicAgent
from src.agents.decision_agent import DecisionAgent
from src.agents.action_item_agent import ActionItemAgent
from src.agents.sentiment_agent import SentimentAgent
from src.agents.summary_agent import SummaryAgent
from src.services.agent_orchestrator import AgentOrchestrator


@pytest.fixture
def large_transcript():
    """Create a large transcript for performance testing."""
    text = " ".join([f"Sentence {i} with some content." for i in range(1000)])
    segments = [
        {"text": f"Sentence {i} with some content.", "start": i * 2.0, "end": (i + 1) * 2.0}
        for i in range(1000)
    ]
    return {"text": text, "segments": segments, "meeting_id": "perf_test"}


@pytest.mark.performance
@pytest.mark.asyncio
async def test_agent_execution_time(large_transcript):
    """Test that agents complete within reasonable time."""
    agents = [
        TopicAgent(token="test_token"),
        DecisionAgent(),
        ActionItemAgent(),
        SentimentAgent(),
        SummaryAgent(token="test_token")
    ]
    
    # Mock LLM calls to avoid actual API calls
    with patch('src.agents.topic_agent.get_mistral_completion', new_callable=AsyncMock) as mock_topic:
        with patch('src.agents.summary_agent.get_mistral_completion', new_callable=AsyncMock) as mock_summary:
            with patch('src.agents.action_item_agent.get_mistral_completion', new_callable=AsyncMock) as mock_action:
                # Mock DecisionAgent's _extract_with_groq method to avoid API calls
                with patch.object(DecisionAgent, '_extract_with_groq', new_callable=AsyncMock) as mock_decision:
                    # Mock sentiment agent to use fallback (faster than API)
                    with patch.object(SentimentAgent, '_analyze_sentiment_hf', return_value=None):
                        mock_topic.return_value = '[{"topic": "Test", "keywords": ["test"], "summary": "Test"}]'
                        mock_summary.side_effect = ["Test summary", "- Test bullet"]
                        mock_action.return_value = "- Action: Test action\n  Assignee: Test\n  Due: Test"
                        mock_decision.return_value = [{"decision": "Test decision"}]
                        
                        max_time = 5.0  # 5 seconds max per agent
                        
                        for agent in agents:
                            start_time = time.time()
                            result = await agent.run(large_transcript)
                            elapsed = time.time() - start_time
                            
                            assert elapsed < max_time, f"{agent.name} took {elapsed:.2f}s, exceeding {max_time}s"
                            assert result is not None


@pytest.mark.performance
@pytest.mark.asyncio
async def test_orchestrator_parallel_execution(temp_storage_dir, mock_transcription_result):
    """Test orchestrator performance with multiple agents."""
    transcription_service = MagicMock()
    # transcribe is a regular method (not async) that returns TranscriptionResult
    transcription_service.transcribe = MagicMock(return_value=mock_transcription_result)
    
    agents = [
        TopicAgent(token="test_token"),
        DecisionAgent(),
        ActionItemAgent(),
        SentimentAgent(),
        SummaryAgent(token="test_token")
    ]
    
    orchestrator = AgentOrchestrator(
        transcription_service=transcription_service,
        agents=agents
    )
    
    with patch('src.agents.topic_agent.get_mistral_completion', new_callable=AsyncMock) as mock_topic:
        with patch('src.agents.summary_agent.get_mistral_completion', new_callable=AsyncMock) as mock_summary:
            with patch('src.agents.action_item_agent.get_mistral_completion', new_callable=AsyncMock) as mock_action:
                with patch.object(DecisionAgent, '_extract_with_groq', new_callable=AsyncMock) as mock_decision:
                    with patch.object(SentimentAgent, '_analyze_sentiment_hf', return_value=None):
                        mock_topic.return_value = '[{"topic": "Test", "keywords": ["test"], "summary": "Test"}]'
                        mock_summary.side_effect = ["Test summary", "- Test bullet"]
                        mock_action.return_value = "- Action: Test action\n  Assignee: Test\n  Due: Test"
                        mock_decision.return_value = [{"decision": "Test decision"}]
                        
                        audio_path = temp_storage_dir / "test_audio.wav"
                        audio_path.touch()
                        
                        start_time = time.time()
                        result = await orchestrator.process(
                            meeting_id="perf_test",
                            audio_path=audio_path
                        )
                        elapsed = time.time() - start_time
                        
                        # Should complete within reasonable time (30 seconds for all agents)
                        max_time = 30.0
                        assert elapsed < max_time, f"Orchestrator took {elapsed:.2f}s, exceeding {max_time}s"
                        assert result is not None


@pytest.mark.performance
def test_sentiment_agent_large_text_performance(large_transcript):
    """Test sentiment agent performance with large text."""
    agent = SentimentAgent()
    
    start_time = time.time()
    # Run synchronously for this test
    result = agent._analyze_sentiment_fallback(large_transcript["text"])
    elapsed = time.time() - start_time
    
    # Should complete within 2 seconds for large text
    max_time = 2.0
    assert elapsed < max_time, f"Sentiment analysis took {elapsed:.2f}s, exceeding {max_time}s"
    assert result is not None

