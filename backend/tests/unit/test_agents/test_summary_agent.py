"""Unit tests for SummaryAgent."""

import pytest
from unittest.mock import AsyncMock, patch

from src.agents.summary_agent import SummaryAgent


@pytest.fixture
def summary_agent():
    """Create a SummaryAgent instance for testing."""
    return SummaryAgent(token="test_token")


@pytest.fixture
def sample_transcript():
    """Sample transcript data for testing."""
    return {
        "text": "Welcome to the quarterly planning meeting. Today we'll discuss our Q2 objectives, budget allocation, and team structure. Let's start with the objectives. Our main goal is to increase revenue by 20%. We need to focus on customer acquisition and retention. The budget for this quarter is $500,000. We'll allocate 60% to marketing, 30% to development, and 10% to operations. The team structure will remain the same, but we'll add two new positions in sales.",
        "segments": [
            {"text": "Welcome to the quarterly planning meeting.", "start": 0.0, "end": 3.0},
            {"text": "Today we'll discuss our Q2 objectives.", "start": 3.0, "end": 6.0},
            {"text": "Our main goal is to increase revenue by 20%.", "start": 6.0, "end": 9.0},
            {"text": "The budget for this quarter is $500,000.", "start": 9.0, "end": 12.0},
        ],
        "meeting_id": "test_meeting_001"
    }


@pytest.mark.asyncio
async def test_summary_agent_run_success(summary_agent, sample_transcript):
    """Test successful summary generation."""
    mock_paragraph = "This meeting covered quarterly planning, including Q2 objectives, budget allocation, and team structure."
    mock_bullets = "- Discussed Q2 objectives\n- Reviewed budget allocation\n- Addressed team structure"
    
    with patch('src.agents.summary_agent.get_mistral_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = [mock_paragraph, mock_bullets]
        
        result = await summary_agent.run(sample_transcript)
        
        assert "summary" in result
        summary = result["summary"]
        assert "extractive" in summary
        assert "abstractive" in summary
        assert "combined" in summary
        
        # Check abstractive components
        assert "paragraph" in summary["abstractive"]
        assert "bullets" in summary["abstractive"]
        assert isinstance(summary["abstractive"]["bullets"], list)


@pytest.mark.asyncio
async def test_summary_agent_run_short_text(summary_agent):
    """Test with very short text."""
    payload = {
        "text": "Hi",
        "segments": [],
        "meeting_id": "test"
    }
    
    result = await summary_agent.run(payload)
    
    assert "summary" in result
    assert isinstance(result["summary"], str)


@pytest.mark.asyncio
async def test_summary_agent_run_long_text_truncation(summary_agent):
    """Test that long text is truncated properly."""
    long_text = " ".join(["word"] * 4000)  # Create very long text
    payload = {
        "text": long_text,
        "segments": [{"text": "test", "start": 0.0, "end": 1.0}],
        "meeting_id": "test"
    }
    
    with patch('src.agents.summary_agent.get_mistral_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = ["Test paragraph", "- Test bullet"]
        
        result = await summary_agent.run(payload)
        
        # Verify LLM was called with truncated text
        assert "summary" in result


@pytest.mark.asyncio
async def test_summary_agent_run_llm_error_fallback(summary_agent, sample_transcript):
    """Test fallback behavior when LLM fails."""
    with patch('src.agents.summary_agent.get_mistral_completion', new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = Exception("API Error")
        
        result = await summary_agent.run(sample_transcript)
        
        # Should still return extractive summary
        assert "summary" in result
        summary = result["summary"]
        assert "extractive" in summary


def test_extract_key_quotes_with_segments(summary_agent, sample_transcript):
    """Test key quote extraction with segments."""
    result = summary_agent._extract_key_quotes(
        sample_transcript["text"],
        segments=sample_transcript["segments"],
        num_quotes=3
    )
    
    assert "excerpts" in result
    assert "text" in result
    assert len(result["excerpts"]) <= 3
    assert all("text" in excerpt for excerpt in result["excerpts"])
    assert all("timestamp" in excerpt for excerpt in result["excerpts"])


def test_extract_key_quotes_without_segments(summary_agent):
    """Test key quote extraction without segments."""
    text = "This is sentence one. This is sentence two. This is sentence three."
    result = summary_agent._extract_key_quotes(text, segments=None, num_quotes=2)
    
    assert "excerpts" in result
    assert "text" in result
    assert len(result["excerpts"]) <= 2


def test_extract_key_quotes_scores_segments(summary_agent, sample_transcript):
    """Test that segments are scored correctly."""
    result = summary_agent._extract_key_quotes(
        sample_transcript["text"],
        segments=sample_transcript["segments"],
        num_quotes=5
    )
    
    # Should prioritize segments with important keywords
    excerpts = result["excerpts"]
    assert len(excerpts) > 0
    
    # Check that excerpts are sorted chronologically
    timestamps = [e["timestamp"] for e in excerpts if e["timestamp"] is not None]
    assert timestamps == sorted(timestamps)

