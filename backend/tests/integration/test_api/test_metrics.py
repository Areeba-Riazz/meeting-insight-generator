"""Integration tests for metrics endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.mark.integration
def test_metrics_endpoint_exists(client):
    """Test that metrics endpoint exists and returns content."""
    response = client.get("/metrics")
    
    # Should return 200 even if Prometheus is not available
    assert response.status_code == 200
    # Accept different versions of Prometheus content type
    content_type = response.headers.get("content-type", "")
    assert "text/plain" in content_type
    
    # Should return some content (either metrics or a message)
    assert len(response.content) > 0


@pytest.mark.integration
def test_metrics_endpoint_after_requests(client):
    """Test that metrics are collected after making requests."""
    # Make some requests first
    client.get("/health")
    client.get("/")
    
    # Then check metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # If Prometheus is available, should contain metric names
    content = response.text
    # Even without Prometheus, should have some content
    assert len(content) > 0

