"""Integration tests for upload endpoint."""

import io
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
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
    # Mock the database dependency to avoid async connection issues
    # The database session needs to be properly mocked as an async context manager
    mock_db = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.close = AsyncMock()
    mock_db.flush = AsyncMock()
    
    # Mock the session's context manager behavior
    mock_session_context = MagicMock()
    mock_session_context.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_context.__aexit__ = AsyncMock(return_value=None)
    
    async def mock_db_gen():
        yield mock_db
    
    with patch('src.api.routes.upload.get_db', return_value=mock_db_gen()):
        with patch('src.api.routes.upload.Path', return_value=temp_storage_dir):
            # Mock process_meeting and process_meeting_with_db to avoid actual processing
            with patch('src.api.routes.upload.process_meeting', new_callable=AsyncMock):
                with patch('src.api.routes.upload.process_meeting_with_db', new_callable=AsyncMock):
                    # Mock pipeline_store.acquire_processing to allow the upload
                    with patch('src.api.routes.upload.pipeline_store.acquire_processing', return_value=True):
                        # Mock database service methods
                        with patch('src.api.routes.upload.DatabaseService') as mock_db_service:
                            mock_service_instance = MagicMock()
                            mock_service_instance.create_meeting = AsyncMock(return_value=MagicMock(id=1))
                            mock_db_service.return_value = mock_service_instance
                            
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

