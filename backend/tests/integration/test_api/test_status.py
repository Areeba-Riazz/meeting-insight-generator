"""Integration tests for status endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.mark.integration
def test_status_endpoint_success(client, temp_storage_dir):
    """Test status endpoint with valid meeting ID."""
    # First, we need to create a meeting in the pipeline store
    # This would typically be done via upload, but for testing we can mock it
    meeting_id = "test_meeting_001"
    
    with patch('src.api.routes.status.pipeline_store') as mock_store:
        mock_store.get_status.return_value = {
            "meeting_id": meeting_id,
            "status": "processing",
            "progress": 50.0
        }
        
        response = client.get(f"/api/v1/status/{meeting_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["meeting_id"] == meeting_id
        assert "status" in data


@pytest.mark.integration
def test_status_endpoint_not_found(client):
    """Test status endpoint with non-existent meeting ID."""
    meeting_id = "nonexistent_meeting"
    
    with patch('src.api.routes.status.pipeline_store') as mock_store:
        mock_store.get_status.return_value = None
        
        response = client.get(f"/api/v1/status/{meeting_id}")
        
        assert response.status_code == 404


@pytest.mark.integration
def test_status_endpoint_completed(client):
    """Test status endpoint for completed meeting."""
    meeting_id = "completed_meeting"
    
    with patch('src.api.routes.status.pipeline_store') as mock_store:
        mock_store.get_status.return_value = {
            "meeting_id": meeting_id,
            "status": "completed",
            "progress": 100.0
        }
        
        response = client.get(f"/api/v1/status/{meeting_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["progress"] == 100.0

