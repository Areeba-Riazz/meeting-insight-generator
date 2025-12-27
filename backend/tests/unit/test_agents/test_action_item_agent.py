"""Unit tests for ActionItemAgent."""

import pytest

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
async def test_action_item_agent_run_success(action_item_agent, sample_transcript):
    """Test successful action item extraction."""
    result = await action_item_agent.run(sample_transcript)
    
    assert "action_items" in result
    assert isinstance(result["action_items"], list)
    assert len(result["action_items"]) > 0
    
    # Check structure of action items
    action_item = result["action_items"][0]
    assert "action" in action_item
    assert "timestamp" in action_item
    assert "evidence" in action_item


@pytest.mark.asyncio
async def test_action_item_agent_run_empty_input(action_item_agent):
    """Test with empty input."""
    payload = {"text": "", "segments": []}
    
    result = await action_item_agent.run(payload)
    
    assert "action_items" in result
    assert result["action_items"] == []


@pytest.mark.asyncio
async def test_action_item_agent_extracts_assignee(action_item_agent, sample_transcript):
    """Test that assignees are extracted correctly."""
    result = await action_item_agent.run(sample_transcript)
    
    # Should find action items with assignees
    action_items = result["action_items"]
    assert any("John" in item.get("action", "") or item.get("assignee") == "John" for item in action_items)


def test_extract_deadline(action_item_agent):
    """Test deadline extraction."""
    text1 = "Complete this by Friday"
    deadline1 = action_item_agent._extract_deadline(text1)
    assert deadline1 is not None
    
    text2 = "Due: next week"
    deadline2 = action_item_agent._extract_deadline(text2)
    assert deadline2 is not None
    
    text3 = "No deadline mentioned"
    deadline3 = action_item_agent._extract_deadline(text3)
    assert deadline3 is None


def test_extract_action_items(action_item_agent):
    """Test action item extraction logic."""
    segments = [
        {"text": "John will send the proposal", "start": 0.0, "end": 3.0},
        {"text": "We need to review the document", "start": 3.0, "end": 6.0},
    ]
    
    action_items = action_item_agent._extract_action_items("", segments)
    
    assert len(action_items) > 0
    assert all("action" in item for item in action_items)
    assert all("timestamp" in item for item in action_items)


def test_extract_action_items_filters_short_matches(action_item_agent):
    """Test that short matches are filtered out."""
    segments = [
        {"text": "We will do it", "start": 0.0, "end": 2.0},  # Too short
        {"text": "We will complete the comprehensive project documentation by next week", "start": 2.0, "end": 5.0},
    ]
    
    action_items = action_item_agent._extract_action_items("", segments)
    
    # Should filter out very short matches
    assert all(len(item["action"]) > 10 for item in action_items)

