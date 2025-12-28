"""
Pytest configuration and shared fixtures.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Generator

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncClient:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def temp_storage_dir() -> Generator[Path, None, None]:
    """Create a temporary storage directory for tests."""
    temp_dir = Path(tempfile.mkdtemp())
    original_storage = Path("storage")
    
    # Create subdirectories
    (temp_dir / "vectors").mkdir(parents=True, exist_ok=True)
    
    yield temp_dir
    
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_audio_file(temp_storage_dir: Path) -> Path:
    """Create a sample audio file for testing."""
    audio_file = temp_storage_dir / "test_audio.wav"
    # Create a minimal WAV file header (44 bytes)
    with open(audio_file, "wb") as f:
        f.write(b"RIFF" + b"\x00" * 40)  # Minimal valid WAV header
    return audio_file


@pytest.fixture
def sample_transcript_data() -> dict:
    """Sample transcript data for testing."""
    return {
        "text": "Welcome to the meeting. Today we'll discuss project planning and budget allocation.",
        "segments": [
            {"text": "Welcome to the meeting.", "start": 0.0, "end": 2.0, "speaker": "SPEAKER_00"},
            {"text": "Today we'll discuss project planning.", "start": 2.0, "end": 5.0, "speaker": "SPEAKER_01"},
            {"text": "Budget allocation is important.", "start": 5.0, "end": 8.0, "speaker": "SPEAKER_00"},
        ],
        "meeting_id": "test_meeting_001"
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("MISTRAL_API_KEY", "test_mistral_key")
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    monkeypatch.setenv("HUGGINGFACE_TOKEN", "test_hf_token")
    monkeypatch.setenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


@pytest.fixture
def mock_transcription_result():
    """Create a mock TranscriptionResult for testing."""
    from src.services.transcription_service import TranscriptionResult, TranscriptionSegment
    
    return TranscriptionResult(
        text="This is a test transcription. Welcome to the meeting.",
        segments=[
            TranscriptionSegment(text="This is a test transcription.", start=0.0, end=2.0, speaker="SPEAKER_00"),
            TranscriptionSegment(text="Welcome to the meeting.", start=2.0, end=4.0, speaker="SPEAKER_01"),
        ],
        model="test_model"
    )
