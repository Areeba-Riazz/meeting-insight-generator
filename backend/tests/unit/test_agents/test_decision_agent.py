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


@pytest.mark.unit
def test_build_extraction_prompt(decision_agent):
    """Test building extraction prompt."""
    short_transcript = "Short transcript"
    prompt = decision_agent._build_extraction_prompt(short_transcript)
    
    assert "transcript" in prompt.lower()
    assert short_transcript in prompt


@pytest.mark.unit
def test_build_extraction_prompt_truncates_long_transcript(decision_agent):
    """Test that prompt truncates very long transcripts."""
    long_transcript = "A" * 15000  # Longer than max_length (10000)
    prompt = decision_agent._build_extraction_prompt(long_transcript)
    
    assert len(prompt) < len(long_transcript) + 500  # Should be truncated
    assert "..." in prompt  # Should have truncation indicator


@pytest.mark.unit
def test_build_transcript_no_segments(decision_agent):
    """Test building transcript when no segments provided."""
    transcript = decision_agent._build_transcript("Test text", [])
    assert transcript == "Test text"


@pytest.mark.unit
def test_build_transcript_empty_segments(decision_agent):
    """Test building transcript with empty segment text."""
    segments = [
        {"text": "   ", "start": 0.0, "speaker": "SPEAKER_00"},
        {"text": "Valid text", "start": 1.0, "speaker": "SPEAKER_01"},
    ]
    transcript = decision_agent._build_transcript("Test", segments)
    
    # Should only include segments with non-empty text
    assert "Valid text" in transcript
    assert "SPEAKER_01" in transcript


@pytest.mark.unit
def test_parse_groq_response_markdown_code_blocks(decision_agent):
    """Test parsing response - markdown cleaning happens in _extract_with_groq, not _parse_groq_response."""
    # _parse_groq_response expects already-cleaned JSON (cleaning happens in _extract_with_groq)
    # So we pass clean JSON here
    content = json.dumps({
        "decisions": [{"decision": "Test", "context": "", "impact": "High", "participants": [], "timestamp": None, "confidence": 0.8, "evidence": ""}]
    })
    
    decisions = decision_agent._parse_groq_response(content)
    assert len(decisions) == 1
    assert decisions[0]["decision"] == "Test"


@pytest.mark.unit
def test_parse_groq_response_participants_as_string(decision_agent):
    """Test parsing when participants is a comma-separated string."""
    content = json.dumps({
        "decisions": [{
            "decision": "Test",
            "context": "",
            "impact": "Medium",
            "participants": "Speaker1, Speaker2",
            "timestamp": None,
            "confidence": 0.8,
            "evidence": ""
        }]
    })
    
    decisions = decision_agent._parse_groq_response(content)
    assert isinstance(decisions[0]["participants"], list)
    assert len(decisions[0]["participants"]) == 2


@pytest.mark.unit
def test_parse_groq_response_invalid_impact(decision_agent):
    """Test parsing normalizes invalid impact levels."""
    content = json.dumps({
        "decisions": [{
            "decision": "Test",
            "context": "",
            "impact": "invalid",
            "participants": [],
            "timestamp": None,
            "confidence": 0.8,
            "evidence": ""
        }]
    })
    
    decisions = decision_agent._parse_groq_response(content)
    assert decisions[0]["impact"] == "Medium"  # Should default to Medium


@pytest.mark.unit
def test_parse_groq_response_invalid_timestamp(decision_agent):
    """Test parsing handles invalid timestamp."""
    content = json.dumps({
        "decisions": [{
            "decision": "Test",
            "context": "",
            "impact": "High",
            "participants": [],
            "timestamp": "invalid",
            "confidence": 0.8,
            "evidence": ""
        }]
    })
    
    decisions = decision_agent._parse_groq_response(content)
    assert decisions[0]["timestamp"] is None


@pytest.mark.unit
def test_parse_groq_response_decision_or_text(decision_agent):
    """Test parsing uses 'text' field if 'decision' is missing."""
    content = json.dumps({
        "decisions": [{
            "text": "Alternative field",
            "context": "",
            "impact": "Low",
            "participants": [],
            "timestamp": None,
            "confidence": 0.8,
            "evidence": ""
        }]
    })
    
    decisions = decision_agent._parse_groq_response(content)
    assert decisions[0]["decision"] == "Alternative field"


@pytest.mark.unit
def test_extract_with_patterns_short_matches(decision_agent):
    """Test pattern extraction filters out short matches."""
    segments = [
        {"text": "We decided to do it.", "start": 0.0, "speaker": "SPEAKER_00"}
    ]
    
    decisions = decision_agent._extract_with_patterns("We decided to do it.", segments)
    # "do it" is too short (< 10 chars), should be filtered
    assert len(decisions) == 0 or all(len(d["decision"]) > 10 for d in decisions)


@pytest.mark.unit
def test_extract_with_patterns_multiple_matches(decision_agent):
    """Test pattern extraction finds multiple decisions."""
    segments = [
        {"text": "We decided to proceed with Option A and the team agreed on the timeline.", "start": 0.0, "speaker": "SPEAKER_00"},
        {"text": "They approved the budget for next quarter.", "start": 10.0, "speaker": "SPEAKER_01"},
    ]
    
    decisions = decision_agent._extract_with_patterns("Test text", segments)
    assert len(decisions) >= 1  # Should find at least one decision


@pytest.mark.asyncio
@pytest.mark.unit
async def test_extract_with_groq_cleans_markdown(decision_agent, sample_transcript):
    """Test that _extract_with_groq cleans markdown code blocks before parsing."""
    decisions_data = {
        "decisions": [{
            "decision": "Test decision",
            "context": "",
            "impact": "High",
            "participants": [],
            "timestamp": None,
            "confidence": 0.8,
            "evidence": ""
        }]
    }
    # Response has markdown code blocks that need to be cleaned
    content_with_markdown = "```json\n" + json.dumps(decisions_data) + "\n```"
    mock_response_data = {
        "choices": [{
            "message": {
                "content": content_with_markdown
            }
        }]
    }
    
    # Mock httpx.AsyncClient - need to mock the context manager properly
    with patch('src.agents.decision_agent.HTTPX_AVAILABLE', True):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.text = ""
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        
        mock_client_class = MagicMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch('src.agents.decision_agent.httpx.AsyncClient', mock_client_class):
            result = await decision_agent._extract_with_groq(
                sample_transcript["text"],
                sample_transcript["segments"]
            )
            
            assert isinstance(result, list)
            # The markdown should be cleaned and JSON parsed successfully
            # The cleaning happens in _extract_with_groq before calling _parse_groq_response
            assert len(result) == 1
            assert result[0]["decision"] == "Test decision"


@pytest.mark.unit
def test_decision_to_dict():
    """Test Decision.to_dict() method."""
    from src.agents.decision_agent import Decision
    
    decision = Decision(
        decision="Test decision",
        context="Context",
        impact="High",
        participants=["Speaker1"],
        timestamp=123.5,
        confidence=0.9,
        evidence="Evidence"
    )
    
    result = decision.to_dict()
    assert isinstance(result, dict)
    assert result["decision"] == "Test decision"
    assert result["impact"] == "High"
    assert result["participants"] == ["Speaker1"]