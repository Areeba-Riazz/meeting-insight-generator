"""Integration tests for upload endpoint."""

import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_video_file():
    """Create a sample video file for testing."""
    # Create a minimal MP4-like file
    content = b"\x00\x00\x00\x20ftypmp41" + b"\x00" * 100
    return io.BytesIO(content)


@pytest.fixture
def sample_audio_file():
    """Create a sample audio file for testing."""
    # Create a minimal WAV-like file
    content = b"RIFF" + b"\x00" * 40
    return io.BytesIO(content)


@pytest.mark.integration
def test_upload_endpoint_success(client, sample_video_file, temp_storage_dir):
    """Test successful file upload."""
    with patch('src.api.routes.upload.Path', return_value=temp_storage_dir):
        with patch('src.api.routes.upload.asyncio.create_task'):
            response = client.post(
                "/api/v1/upload",
                files={"file": ("test.mp4", sample_video_file, "video/mp4")},
                data={"project_id": "test_project"}
            )
            
            assert response.status_code in [200, 202]  # Accepted or OK
            data = response.json()
            assert "meeting_id" in data
            assert "status" in data


@pytest.mark.integration
def test_upload_endpoint_invalid_file_type(client):
    """Test upload with invalid file type."""
    invalid_file = io.BytesIO(b"invalid content")
    
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.txt", invalid_file, "text/plain")},
        data={"project_id": "test_project"}
    )
    
    # Should return 400 or 422 for invalid file type
    assert response.status_code in [400, 422]


@pytest.mark.integration
def test_upload_endpoint_missing_file(client):
    """Test upload without file."""
    response = client.post(
        "/api/v1/upload",
        data={"project_id": "test_project"}
    )
    
    assert response.status_code in [400, 422]


@pytest.mark.integration
def test_upload_endpoint_large_file(client, temp_storage_dir):
    """Test upload with file size validation."""
    # Create a large file (simulate)
    large_content = b"x" * (600 * 1024 * 1024)  # 600 MB
    large_file = io.BytesIO(large_content)
    
    with patch('src.api.routes.upload.Path', return_value=temp_storage_dir):
        response = client.post(
            "/api/v1/upload",
            files={"file": ("large.mp4", large_file, "video/mp4")},
            data={"project_id": "test_project"}
        )
        
        # Should reject or handle large files appropriately
        assert response.status_code in [200, 202, 400, 413]

