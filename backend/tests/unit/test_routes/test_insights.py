"""Unit tests for insights route."""

import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException

from src.api.routes.insights import get_insights


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.execute = AsyncMock()
    return db


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_insights_success_from_pipeline_store(mock_db):
    """Test successful insights retrieval from pipeline store."""
    meeting_id_str = "test_meeting_123"
    
    # Mock pipeline store result
    mock_pipeline_result = {
        "topics": [{"topic": "Topic 1"}],
        "decisions": [{"decision": "Decision 1"}],
        "action_items": [{"action": "Action 1"}],
        "sentiment": {"overall": "positive"},
        "summary": "Meeting summary"
    }
    
    # Mock database - no meeting found by file_path
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    with patch('src.api.routes.insights.pipeline_store') as mock_store:
        mock_store.get_result.return_value = mock_pipeline_result
        
        result = await get_insights(meeting_id_str, mock_db)
        
        assert result["meeting_id"] == meeting_id_str
        assert "insights" in result
        assert result["insights"] == mock_pipeline_result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_insights_not_found(mock_db):
    """Test insights retrieval for non-existent meeting."""
    meeting_id_str = "nonexistent_meeting"
    
    # Mock database - no meeting found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    with patch('src.api.routes.insights.pipeline_store') as mock_store:
        mock_store.get_result.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_insights(meeting_id_str, mock_db)
        
        assert exc_info.value.status_code == 404


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_insights_processing(mock_db):
    """Test insights retrieval when meeting is still processing."""
    meeting_id_str = "processing_meeting"
    
    # Mock database - no meeting found, fallback to pipeline store
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    with patch('src.api.routes.insights.pipeline_store') as mock_store:
        mock_store.get_result.return_value = None
        mock_store.get_status.return_value = "processing"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_insights(meeting_id_str, mock_db)
        
        assert exc_info.value.status_code == 404


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_insights_empty_result(mock_db):
    """Test insights retrieval - empty result raises 404."""
    meeting_id_str = "empty_meeting"
    
    # Mock database - no meeting found by file_path
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    with patch('src.api.routes.insights.pipeline_store') as mock_store:
        # None means not found, empty dict would be truthy but None means no result
        mock_store.get_result.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_insights(meeting_id_str, mock_db)
        
        assert exc_info.value.status_code == 404

