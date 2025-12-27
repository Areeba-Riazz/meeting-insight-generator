"""Integration tests for insights endpoint."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.main import app


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
    
    with patch('src.api.routes.insights.pipeline_store') as mock_store:
        mock_store.get_results.return_value = mock_insights
        
        response = client.get(f"/api/v1/insights/{meeting_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["meeting_id"] == meeting_id
        assert "insights" in data


@pytest.mark.integration
def test_insights_endpoint_not_found(client):
    """Test insights endpoint with non-existent meeting ID."""
    meeting_id = "nonexistent_meeting"
    
    with patch('src.api.routes.insights.pipeline_store') as mock_store:
        mock_store.get_results.return_value = None
        
        response = client.get(f"/api/v1/insights/{meeting_id}")
        
        assert response.status_code == 404


@pytest.mark.integration
def test_insights_endpoint_processing(client):
    """Test insights endpoint when meeting is still processing."""
    meeting_id = "processing_meeting"
    
    with patch('src.api.routes.insights.pipeline_store') as mock_store:
        mock_store.get_results.return_value = None
        mock_store.get_status.return_value = {"status": "processing"}
        
        response = client.get(f"/api/v1/insights/{meeting_id}")
        
        # Should return 202 or 404 depending on implementation
        assert response.status_code in [202, 404]

