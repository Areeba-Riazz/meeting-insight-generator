"""Unit tests for status route."""

import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException

from src.api.routes.status import get_status


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.execute = AsyncMock()
    return db


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_status_success(mock_db):
    """Test successful status retrieval from pipeline store."""
    meeting_id = "test_meeting_123"
    meeting_uuid = uuid.uuid4()
    
    # Mock database - meeting not found initially
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    mock_store = MagicMock()
    mock_store.get_status.return_value = "processing"
    mock_store.get_progress.return_value = 50.0
    mock_store.get_stage.return_value = "Transcribing"
    
    with patch('src.api.routes.status.pipeline_store', mock_store):
        result = await get_status(meeting_id, mock_db)
        
        assert result["meeting_id"] == meeting_id
        assert result["status"] == "processing"
        assert result["progress"] == 50.0
        assert result["stage"] == "Transcribing"
        mock_store.get_status.assert_called_once_with(meeting_id)
        mock_store.get_progress.assert_called_once_with(meeting_id)
        mock_store.get_stage.assert_called_once_with(meeting_id)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_status_not_found(mock_db):
    """Test status retrieval for non-existent meeting."""
    meeting_id = "nonexistent_meeting"
    
    # Mock database - meeting not found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    mock_store = MagicMock()
    mock_store.get_status.return_value = None
    
    with patch('src.api.routes.status.pipeline_store', mock_store):
        with pytest.raises(HTTPException) as exc_info:
            await get_status(meeting_id, mock_db)
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_status_no_progress(mock_db):
    """Test status retrieval when progress is None."""
    meeting_id = "test_meeting_123"
    
    # Mock database - meeting not found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    mock_store = MagicMock()
    mock_store.get_status.return_value = "processing"
    mock_store.get_progress.return_value = None  # Returns None directly
    mock_store.get_stage.return_value = None     # Returns None directly
    
    with patch('src.api.routes.status.pipeline_store', mock_store):
        result = await get_status(meeting_id, mock_db)
        
        assert result["meeting_id"] == meeting_id
        assert result["status"] == "processing"
        # When meeting not found in DB, pipeline_store values are returned directly (lines 48-49, 54-55)
        # So progress and stage can be None if pipeline_store returns None - they're passed through as-is
        assert result["progress"] is None  # Can be None when returned directly from pipeline_store
        assert result["stage"] is None     # Can be None when returned directly from pipeline_store


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_status_completed(mock_db):
    """Test status retrieval for completed meeting."""
    meeting_id = "completed_meeting"
    
    # Mock database - meeting not found, fallback to pipeline store
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    mock_store = MagicMock()
    mock_store.get_status.return_value = "completed"
    mock_store.get_progress.return_value = 100.0
    mock_store.get_stage.return_value = "Completed"
    
    with patch('src.api.routes.status.pipeline_store', mock_store):
        result = await get_status(meeting_id, mock_db)
        
        assert result["status"] == "completed"
        assert result["progress"] == 100.0
        assert result["stage"] == "Completed"

