"""
Pytest configuration and shared fixtures.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

# Add fixtures here as needed
# Example:
# @pytest.fixture
# async def client():
#     async with AsyncClient(app=app, base_url="http://test") as ac:
#         yield ac

