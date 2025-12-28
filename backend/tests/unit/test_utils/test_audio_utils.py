"""Unit tests for audio utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.audio_utils import preprocess_audio


@pytest.fixture
def sample_audio_file(temp_storage_dir):
    """Create a sample audio file for testing."""
    audio_file = temp_storage_dir / "test_audio.wav"
    # Create a minimal WAV file
    with open(audio_file, "wb") as f:
        f.write(b"RIFF" + b"\x00" * 40)
    return audio_file


@pytest.fixture
def sample_video_file(temp_storage_dir):
    """Create a sample video file for testing."""
    video_file = temp_storage_dir / "test_video.mp4"
    # Create a minimal MP4 file
    with open(video_file, "wb") as f:
        f.write(b"\x00\x00\x00\x20ftypmp41" + b"\x00" * 100)
    return video_file


@pytest.mark.unit
def test_preprocess_audio_wav_file(sample_audio_file):
    """Test preprocessing a WAV audio file."""
    # Mock AudioSegment to avoid actual audio processing
    mock_audio = MagicMock()
    mock_audio.set_frame_rate.return_value = mock_audio
    mock_audio.set_channels.return_value = mock_audio
    
    with patch('src.utils.audio_utils.AudioSegment') as mock_segment:
        mock_segment.from_file.return_value = mock_audio
        with patch('tempfile.gettempdir', return_value=str(sample_audio_file.parent)):
            result = preprocess_audio(sample_audio_file, target_rate=16000)
            
            # Verify AudioSegment was called
            mock_segment.from_file.assert_called_once()
            mock_audio.set_frame_rate.assert_called_once_with(16000)
            mock_audio.set_channels.assert_called_once_with(1)
            mock_audio.export.assert_called_once()


@pytest.mark.unit
def test_preprocess_audio_video_file(sample_video_file):
    """Test preprocessing a video file (should extract audio first)."""
    mock_audio = MagicMock()
    mock_audio.set_frame_rate.return_value = mock_audio
    mock_audio.set_channels.return_value = mock_audio
    mock_extracted_path = Path("/tmp/extracted.wav")
    
    with patch('src.utils.audio_utils.extract_audio_from_video') as mock_extract:
        mock_extract.return_value = mock_extracted_path
        
        with patch('src.utils.audio_utils.AudioSegment') as mock_segment:
            mock_segment.from_file.return_value = mock_audio
            with patch('tempfile.gettempdir', return_value="/tmp"):
                result = preprocess_audio(sample_video_file, target_rate=16000)
                
                # Verify extract_audio_from_video was called
                mock_extract.assert_called_once_with(sample_video_file, target_rate=16000)
                mock_segment.from_file.assert_called_once()


@pytest.mark.unit
def test_preprocess_audio_custom_rate(sample_audio_file):
    """Test preprocessing with custom sample rate."""
    mock_audio = MagicMock()
    mock_audio.set_frame_rate.return_value = mock_audio
    mock_audio.set_channels.return_value = mock_audio
    
    with patch('src.utils.audio_utils.AudioSegment') as mock_segment:
        mock_segment.from_file.return_value = mock_audio
        with patch('tempfile.gettempdir', return_value=str(sample_audio_file.parent)):
            result = preprocess_audio(sample_audio_file, target_rate=22050)
            
            mock_audio.set_frame_rate.assert_called_once_with(22050)
