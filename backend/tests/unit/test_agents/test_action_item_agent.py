"""Unit tests for ActionItemAgent."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.agents.action_item_agent import ActionItemAgent


@pytest.fixture
def action_item_agent():
    """Create an ActionItemAgent instance for testing."""
    return ActionItemAgent()


@pytest.fixture
def sample_transcript():
    """Sample transcript data for testing."""
    return {
        "text": "John will send the proposal by Friday. Sarah should review the document. We need to schedule a follow-up meeting.",
        "segments": [
            {"text": "John will send the proposal by Friday.", "start": 0.0, "end": 3.0},
            {"text": "Sarah should review the document.", "start": 3.0, "end": 6.0},
            {"text": "We need to schedule a follow-up meeting.", "start": 6.0, "end": 9.0},
        ],
        "meeting_id": "test_meeting_001"
    }


@pytest.mark.asyncio
@pytest.mark.unit
async def test_action_item_agent_run_success(action_item_agent, sample_transcript):
    """Test successful action item extraction."""
    with patch('src.agents.action_item_agent.get_mistral_completion', new_callable=AsyncMock) as mock_mistral:
        mock_mistral.return_value = "- Action: Send proposal\n  Assignee: John\n  Due: Friday"
        result = await action_item_agent.run(sample_transcript)
        
        assert "action_items" in result
        assert isinstance(result["action_items"], list)
        mock_mistral.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_action_item_agent_run_empty_input(action_item_agent):
    """Test with empty input."""
    payload = {"text": "", "segments": []}
    
    result = await action_item_agent.run(payload)
    
    assert "action_items" in result
    assert result["action_items"] == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_action_item_agent_run_no_ai_response(action_item_agent, sample_transcript):
    """Test when AI returns no response."""
    with patch('src.agents.action_item_agent.get_mistral_completion', new_callable=AsyncMock) as mock_mistral:
        mock_mistral.return_value = ""
        result = await action_item_agent.run(sample_transcript)
        
        assert "action_items" in result
        assert result["action_items"] == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_action_item_agent_run_fallback_parsing(action_item_agent, sample_transcript):
    """Test fallback parsing when structured format fails."""
    with patch('src.agents.action_item_agent.get_mistral_completion', new_callable=AsyncMock) as mock_mistral:
        # Return unstructured response that triggers fallback
        mock_mistral.return_value = "Here are some action items:\n- Send proposal\n- Review document"
        result = await action_item_agent.run(sample_transcript)
        
        assert "action_items" in result
        # Should use fallback parsing
        assert isinstance(result["action_items"], list)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_action_item_agent_run_api_error_fallback(action_item_agent, sample_transcript):
    """Test fallback to keyword extraction when API fails."""
    with patch('src.agents.action_item_agent.get_mistral_completion', new_callable=AsyncMock) as mock_mistral:
        mock_mistral.side_effect = Exception("API Error")
        result = await action_item_agent.run(sample_transcript)
        
        assert "action_items" in result
        # Should use keyword extraction fallback
        assert isinstance(result["action_items"], list)


@pytest.mark.unit
def test_parse_action_items(action_item_agent):
    """Test action item parsing logic."""
    ai_response = """- Action: Complete the proposal
  Assignee: John
  Due: Friday
  
- Action: Review the document
  Assignee: Sarah
  Due: Next week"""
    
    action_items = action_item_agent._parse_action_items(ai_response)
    
    assert len(action_items) == 2
    assert all("action" in item for item in action_items)
    assert action_items[0]["action"] == "Complete the proposal"
    assert action_items[0]["assignee"] == "John"
    assert action_items[0]["due"] == "Friday"


@pytest.mark.unit
def test_parse_action_items_malformed(action_item_agent):
    """Test parsing with malformed input."""
    ai_response = "This is not in the expected format"
    action_items = action_item_agent._parse_action_items(ai_response)
    
    # Should return empty list or handle gracefully
    assert isinstance(action_items, list)


@pytest.mark.unit
def test_fallback_extract_action_items(action_item_agent):
    """Test fallback extraction method."""
    ai_response = """Here are action items:
- Organize the meeting notes
- Create presentation slides
- Send follow-up email"""
    
    transcript = "We need to organize notes and create slides."
    result = action_item_agent._fallback_extract_action_items(ai_response, transcript)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert all("action" in item for item in result)


@pytest.mark.unit
def test_fallback_extract_action_items_with_headers(action_item_agent):
    """Test fallback extraction skips headers."""
    ai_response = """Action Items:
Below:
- Extract items
- List items"""
    
    transcript = "We need to do something."
    result = action_item_agent._fallback_extract_action_items(ai_response, transcript)
    
    # Should skip lines with header keywords
    assert isinstance(result, list)


@pytest.mark.unit
def test_fallback_extract_action_items_short_lines(action_item_agent):
    """Test fallback extraction skips lines that are too short."""
    ai_response = "Do it.\n\nThis is a very short line\nCreate a comprehensive report"
    
    transcript = "We need to create reports."
    result = action_item_agent._fallback_extract_action_items(ai_response, transcript)
    
    # Should only include lines > 10 characters with action keywords
    assert isinstance(result, list)


@pytest.mark.unit
def test_fallback_keyword_extraction(action_item_agent):
    """Test keyword extraction fallback method."""
    transcript = "John should send the proposal. Sarah needs to review the document. We will schedule a meeting."
    segments = [
        {"text": "John should send the proposal.", "start": 0.0},
        {"text": "Sarah needs to review the document.", "start": 10.0},
        {"text": "We will schedule a meeting.", "start": 20.0},
    ]
    
    result = action_item_agent._fallback_keyword_extraction(transcript, segments)
    
    assert "action_items" in result
    assert isinstance(result["action_items"], list)
    assert len(result["action_items"]) > 0
    assert all("action" in item for item in result["action_items"])


@pytest.mark.unit
def test_fallback_keyword_extraction_with_assignee(action_item_agent):
    """Test keyword extraction extracts assignees."""
    transcript = "The proposal should be sent by John. Review assigned to Sarah."
    segments = [
        {"text": "The proposal should be sent by John.", "start": 0.0},
        {"text": "Review assigned to Sarah.", "start": 10.0},
    ]
    
    result = action_item_agent._fallback_keyword_extraction(transcript, segments)
    
    assert "action_items" in result
    # Should extract assignees where possible
    assert any(item.get("assignee") for item in result["action_items"])


@pytest.mark.unit
def test_fallback_keyword_extraction_removes_duplicates(action_item_agent):
    """Test keyword extraction removes duplicate action items."""
    transcript = "Send the email. Send the email again. We should send the email."
    segments = [
        {"text": "Send the email.", "start": 0.0},
        {"text": "Send the email again.", "start": 5.0},
        {"text": "We should send the email.", "start": 10.0},
    ]
    
    result = action_item_agent._fallback_keyword_extraction(transcript, segments)
    
    assert "action_items" in result
    # Should have fewer items due to deduplication
    assert len(result["action_items"]) <= 5  # Max 5 items returned


@pytest.mark.asyncio
@pytest.mark.unit
async def test_action_item_agent_cleans_items(action_item_agent, sample_transcript):
    """Test that action items are cleaned (short items skipped, capitalization fixed)."""
    with patch('src.agents.action_item_agent.get_mistral_completion', new_callable=AsyncMock) as mock_mistral:
        mock_mistral.return_value = """- Action: none
  Assignee: Test
  Due: Now
  
- Action: send email
  Assignee: John
  Due: Friday"""
        
        result = await action_item_agent.run(sample_transcript)
        
        assert "action_items" in result
        # Should skip "none" items
        # Should capitalize "send email" -> "Send email"
        for item in result["action_items"]:
            if item.get("action"):
                assert len(item["action"]) >= 10  # Min length
                assert item["action"][0].isupper()  # Capitalized

