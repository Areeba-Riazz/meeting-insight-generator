"""Integration tests for insights endpoint."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from src.main import app
from src.core.database import get_db


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.mark.integration
def test_insights_endpoint_success(client, temp_storage_dir):
    """Test insights endpoint with valid meeting ID."""
    meeting_id = "test_meeting_001"
    
    mock_insights = {
        "meeting_id": meeting_id,
        "transcript": {
            "text": "Test transcript",
            "segments": []
        },
        "topics": [],
        "decisions": [],
        "action_items": [],
        "sentiment": {"overall": "Neutral", "score": 0.5},
        "summary": {"combined": "Test summary"}
    }
    
    # Mock database dependency to avoid async connection issues
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    async def mock_db_gen():
        yield mock_db
    
    # Use dependency override instead of patching
    async def override_get_db():
        async for session in mock_db_gen():
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    try:
        with patch('src.api.routes.insights.pipeline_store') as mock_store:
            mock_store.get_result.return_value = mock_insights
            
            response = client.get(f"/api/v1/insights/{meeting_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["meeting_id"] == meeting_id
            assert "insights" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.integration
def test_insights_endpoint_not_found(client):
    """Test insights endpoint with non-existent meeting ID."""
    meeting_id = "nonexistent_meeting"
    
    # Mock database dependency to avoid async connection issues
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    async def mock_db_gen():
        yield mock_db
    
    # Use dependency override instead of patching
    async def override_get_db():
        async for session in mock_db_gen():
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    try:
        with patch('src.api.routes.insights.pipeline_store') as mock_store:
            mock_store.get_result.return_value = None
            
            response = client.get(f"/api/v1/insights/{meeting_id}")
            
            assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.integration
def test_insights_endpoint_processing(client):
    """Test insights endpoint when meeting is still processing."""
    meeting_id = "processing_meeting"

    # Mock database dependency to avoid async connection issues
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    async def mock_db_gen():
        yield mock_db
    
    # Use dependency override instead of patching
    async def override_get_db():
        async for session in mock_db_gen():
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    try:
        with patch('src.api.routes.insights.pipeline_store') as mock_store:
            mock_store.get_result.return_value = None
            
            response = client.get(f"/api/v1/insights/{meeting_id}")
            
            # Should return 404 when not found
            assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()

