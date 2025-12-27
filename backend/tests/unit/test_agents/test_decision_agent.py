"""Unit tests for DecisionAgent."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.decision_agent import DecisionAgent


@pytest.fixture
def decision_agent():
    """Create a DecisionAgent instance for testing."""
    with patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'}):
        return DecisionAgent()


@pytest.fixture
def decision_agent_no_api():
    """Create a DecisionAgent without API key."""
    with patch.dict('os.environ', {}, clear=True):
        return DecisionAgent()


@pytest.fixture
def sample_transcript():
    """Sample transcript data for testing."""
    return {
        "text": "We decided to proceed with Option A. The team agreed on the timeline. We will implement this next week.",
        "segments": [
            {"text": "We decided to proceed with Option A.", "start": 0.0, "end": 3.0, "speaker": "SPEAKER_00"},
            {"text": "The team agreed on the timeline.", "start": 3.0, "end": 6.0, "speaker": "SPEAKER_01"},
            {"text": "We will implement this next week.", "start": 6.0, "end": 9.0, "speaker": "SPEAKER_00"},
        ],
        "meeting_id": "test_meeting_001"
    }


@pytest.mark.asyncio
async def test_decision_agent_run_with_api_success(decision_agent, sample_transcript):
    """Test successful decision extraction with Groq API."""
    mock_groq_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "decisions": [
                        {
                            "decision": "Proceed with Option A",
                            "context": "Technical discussion",
                            "impact": "High",
                            "participants": ["SPEAKER_00"],
                            "timestamp": 0.0,
                            "confidence": 0.9,
                            "evidence": "We decided to proceed with Option A"
                        }
                    ]
                })
            }
        }]
    }
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_groq_response
        mock_response.text = ""
        
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aexit__.return_value = None
        mock_client.return_value = mock_client_instance
        
        result = await decision_agent.run(sample_transcript)
        
        assert "decisions" in result
        assert len(result["decisions"]) > 0
        assert result["decisions"][0]["decision"] == "Proceed with Option A"


@pytest.mark.asyncio
async def test_decision_agent_run_fallback_pattern_matching(decision_agent_no_api, sample_transcript):
    """Test fallback to pattern matching when API is not available."""
    result = await decision_agent_no_api.run(sample_transcript)
    
    assert "decisions" in result
    # Pattern matching should find some decisions
    assert isinstance(result["decisions"], list)


@pytest.mark.asyncio
async def test_decision_agent_run_api_error_fallback(decision_agent, sample_transcript):
    """Test fallback when API call fails."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aexit__.return_value = None
        mock_client.return_value = mock_client_instance
        
        result = await decision_agent.run(sample_transcript)
        
        # Should fallback to pattern matching
        assert "decisions" in result
        assert isinstance(result["decisions"], list)


@pytest.mark.asyncio
async def test_decision_agent_run_empty_input(decision_agent):
    """Test with empty input."""
    payload = {"text": "", "segments": []}
    
    result = await decision_agent.run(payload)
    
    assert "decisions" in result
    assert result["decisions"] == []


def test_extract_with_patterns(decision_agent_no_api, sample_transcript):
    """Test pattern-based decision extraction."""
    decisions = decision_agent_no_api._extract_with_patterns(
        sample_transcript["text"],
        sample_transcript["segments"]
    )
    
    assert isinstance(decisions, list)
    # Should find at least one decision
    assert len(decisions) > 0
    assert "decision" in decisions[0]
    assert "timestamp" in decisions[0]


def test_build_transcript(decision_agent):
    """Test transcript building with segments."""
    segments = [
        {"text": "Hello", "start": 0.0, "speaker": "SPEAKER_00"},
        {"text": "World", "start": 2.0, "speaker": "SPEAKER_01"},
    ]
    
    transcript = decision_agent._build_transcript("Hello World", segments)
    
    assert "SPEAKER_00" in transcript
    assert "SPEAKER_01" in transcript
    assert "0.0s" in transcript


def test_parse_groq_response(decision_agent):
    """Test parsing of Groq API response."""
    content = json.dumps({
        "decisions": [
            {
                "decision": "Test decision",
                "context": "Test context",
                "impact": "High",
                "participants": "Speaker1, Speaker2",
                "timestamp": 123.5,
                "confidence": 0.9,
                "evidence": "Test evidence"
            }
        ]
    })
    
    decisions = decision_agent._parse_groq_response(content)
    
    assert len(decisions) == 1
    assert decisions[0]["decision"] == "Test decision"
    assert isinstance(decisions[0]["participants"], list)
    assert len(decisions[0]["participants"]) == 2


def test_parse_groq_response_invalid_json(decision_agent):
    """Test handling of invalid JSON in Groq response."""
    with pytest.raises(ValueError):
        decision_agent._parse_groq_response("invalid json")

