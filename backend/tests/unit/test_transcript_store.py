"""Unit tests for transcript store."""

import pytest
import json
from pathlib import Path

from src.services.transcript_store import TranscriptStore
from src.services.transcription_service import TranscriptionResult, TranscriptionSegment


@pytest.fixture
def transcript_store(temp_storage_dir):
    """Create a TranscriptStore instance for testing."""
    return TranscriptStore(base_path=temp_storage_dir)


@pytest.fixture
def sample_transcript():
    """Create a sample transcript for testing."""
    return TranscriptionResult(
        text="Hello world. This is a test.",
        segments=[
            TranscriptionSegment(text="Hello world.", start=0.0, end=2.0, speaker="SPEAKER_00"),
            TranscriptionSegment(text="This is a test.", start=2.0, end=4.0, speaker="SPEAKER_01"),
        ],
        model="test_model"
    )


@pytest.mark.unit
def test_transcript_store_init(transcript_store, temp_storage_dir):
    """Test TranscriptStore initialization."""
    assert transcript_store.base_path == temp_storage_dir
    assert temp_storage_dir.exists()


@pytest.mark.unit
def test_save_transcript(transcript_store, sample_transcript):
    """Test saving a transcript."""
    meeting_id = "test_meeting_001"
    
    transcript_path = transcript_store.save_transcript(meeting_id, sample_transcript)
    
    assert transcript_path.exists()
    assert transcript_path.name == "transcript.json"
    
    # Verify content
    with open(transcript_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data["text"] == "Hello world. This is a test."
    assert data["model"] == "test_model"
    assert len(data["segments"]) == 2
    assert data["segments"][0]["text"] == "Hello world."
    assert data["segments"][0]["speaker"] == "SPEAKER_00"


@pytest.mark.unit
def test_save_diarized_transcript(transcript_store, sample_transcript):
    """Test saving diarized transcript."""
    meeting_id = "test_meeting_002"
    
    diarized_path = transcript_store.save_diarized_transcript(meeting_id, sample_transcript)
    
    assert diarized_path.exists()
    assert diarized_path.name == "diarized_transcript.txt"
    
    # Verify content
    content = diarized_path.read_text(encoding="utf-8")
    assert "SPEAKER_00" in content
    assert "SPEAKER_01" in content
    assert "Hello world." in content
    assert "This is a test." in content


@pytest.mark.unit
def test_load_transcript(transcript_store, sample_transcript):
    """Test loading a transcript."""
    meeting_id = "test_meeting_003"
    
    # Save first
    transcript_store.save_transcript(meeting_id, sample_transcript)
    
    # Load
    loaded_data = transcript_store.load_transcript(meeting_id)
    
    assert loaded_data is not None
    assert loaded_data["text"] == "Hello world. This is a test."
    assert loaded_data["model"] == "test_model"
    assert len(loaded_data["segments"]) == 2


@pytest.mark.unit
def test_load_transcript_not_found(transcript_store):
    """Test loading a non-existent transcript."""
    result = transcript_store.load_transcript("nonexistent_meeting")
    assert result is None


@pytest.mark.unit
def test_load_diarized_transcript(transcript_store, sample_transcript):
    """Test loading diarized transcript."""
    meeting_id = "test_meeting_004"
    
    # Save first
    transcript_store.save_diarized_transcript(meeting_id, sample_transcript)
    
    # Load
    content = transcript_store.load_diarized_transcript(meeting_id)
    
    assert content is not None
    assert isinstance(content, str)
    assert "SPEAKER_00" in content
    assert "Hello world." in content


@pytest.mark.unit
def test_load_diarized_transcript_not_found(transcript_store):
    """Test loading a non-existent diarized transcript."""
    result = transcript_store.load_diarized_transcript("nonexistent_meeting")
    assert result is None


@pytest.mark.unit
def test_format_time(transcript_store):
    """Test time formatting."""
    assert transcript_store._format_time(0.0) == "00:00"
    assert transcript_store._format_time(65.5) == "01:05"
    assert transcript_store._format_time(125.0) == "02:05"


@pytest.mark.unit
def test_save_transcript_segments_without_speaker(transcript_store):
    """Test saving transcript with segments without speaker."""
    transcript = TranscriptionResult(
        text="Hello world.",
        segments=[
            TranscriptionSegment(text="Hello world.", start=0.0, end=2.0, speaker=None),
        ],
        model="test_model"
    )
    
    meeting_id = "test_meeting_005"
    transcript_store.save_transcript(meeting_id, transcript)
    
    # Should handle None speaker gracefully
    loaded = transcript_store.load_transcript(meeting_id)
    assert loaded is not None
    assert loaded["segments"][0].get("speaker") is None

