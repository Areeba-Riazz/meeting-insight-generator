"""Unit tests for TopicAgent."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.topic_agent import TopicAgent


@pytest.fixture
def topic_agent():
    """Create a TopicAgent instance for testing."""
    return TopicAgent(token="test_token")


@pytest.fixture
def sample_transcript():
    """Sample transcript data for testing."""
    return {
        "text": "Welcome to the meeting. Today we'll discuss project planning, budget allocation, and team coordination. Let's start with project planning.",
        "segments": [
            {"text": "Welcome to the meeting.", "start": 0.0, "end": 2.0},
            {"text": "Today we'll discuss project planning.", "start": 2.0, "end": 5.0},
            {"text": "Budget allocation is important.", "start": 5.0, "end": 8.0},
            {"text": "Team coordination needs improvement.", "start": 8.0, "end": 11.0},
        ],
        "meeting_id": "test_meeting_001"
    }


@pytest.mark.asyncio
async def test_topic_agent_run_success(topic_agent, sample_transcript):
    """Test successful topic extraction."""
    mock_response = json.dumps([
        {
            "topic": "Project Planning",
            "keywords": ["project", "planning"],
            "summary": "Discussion about project planning strategies."
        },
        {
            "topic": "Budget Allocation",
            "keywords": ["budget", "allocation"],
            "summary": "Review of budget allocation process."
        }
    ])
    
    with patch('src.agents.topic_agent.get_mistral_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_response
        
        result = await topic_agent.run(sample_transcript)
        
        assert "topics" in result
        assert len(result["topics"]) == 2
        assert result["topics"][0]["topic"] == "Project Planning"
        assert "start" in result["topics"][0]
        assert "end" in result["topics"][0]
        assert "summary" in result["topics"][0]


@pytest.mark.asyncio
async def test_topic_agent_run_short_text(topic_agent):
    """Test topic agent with very short text."""
    payload = {
        "text": "Hi",
        "segments": [],
        "meeting_id": "test"
    }
    
    result = await topic_agent.run(payload)
    
    assert "topics" in result
    assert result["topics"] == []


@pytest.mark.asyncio
async def test_topic_agent_run_long_text_truncation(topic_agent):
    """Test that long text is truncated properly."""
    long_text = " ".join(["word"] * 3000)  # Create very long text
    payload = {
        "text": long_text,
        "segments": [{"text": "test", "start": 0.0, "end": 1.0}],
        "meeting_id": "test"
    }
    
    with patch('src.agents.topic_agent.get_mistral_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = json.dumps([{"topic": "Test", "keywords": ["test"], "summary": "Test summary"}])
        
        result = await topic_agent.run(payload)
        
        # Verify LLM was called with truncated text
        call_args = mock_llm.call_args
        assert "..." in call_args[1]["prompt"] or len(call_args[1]["prompt"]) < len(long_text)


@pytest.mark.asyncio
async def test_topic_agent_run_llm_error_fallback(topic_agent, sample_transcript):
    """Test fallback behavior when LLM fails."""
    with patch('src.agents.topic_agent.get_mistral_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = Exception("API Error")
        
        result = await topic_agent.run(sample_transcript)
        
        # Should return fallback topic
        assert "topics" in result
        assert len(result["topics"]) > 0
        assert result["topics"][0]["topic"] == "Meeting Discussion"


@pytest.mark.asyncio
async def test_topic_agent_run_invalid_json_response(topic_agent, sample_transcript):
    """Test handling of invalid JSON response from LLM."""
    invalid_response = "This is not valid JSON [invalid"
    
    with patch('src.agents.topic_agent.get_mistral_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = invalid_response
        
        result = await topic_agent.run(sample_transcript)
        
        # Should fallback to generic topic
        assert "topics" in result
        assert len(result["topics"]) > 0


def test_find_topic_timestamps(topic_agent):
    """Test timestamp finding for topics."""
    segments = [
        {"text": "We discussed project planning", "start": 0.0, "end": 3.0},
        {"text": "Budget allocation is next", "start": 3.0, "end": 6.0},
        {"text": "Project planning details", "start": 6.0, "end": 9.0},
    ]
    
    keywords = ["project", "planning"]
    start, end = topic_agent._find_topic_timestamps(keywords, segments)
    
    assert start == 0.0
    assert end == 9.0


def test_find_topic_timestamps_no_match(topic_agent):
    """Test timestamp finding when no keywords match."""
    segments = [
        {"text": "We discussed something else", "start": 0.0, "end": 3.0},
    ]
    
    keywords = ["nonexistent", "keywords"]
    start, end = topic_agent._find_topic_timestamps(keywords, segments)
    
    assert start == 0
    assert end == 0

