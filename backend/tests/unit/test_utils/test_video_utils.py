"""Unit tests for video utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.video_utils import extract_audio_from_video


@pytest.fixture
def sample_video_file(temp_storage_dir):
    """Create a sample video file for testing."""
    video_file = temp_storage_dir / "test_video.mp4"
    # Create a minimal MP4 file
    with open(video_file, "wb") as f:
        f.write(b"\x00\x00\x00\x20ftypmp41" + b"\x00" * 100)
    return video_file


@pytest.mark.unit
def test_extract_audio_from_video(sample_video_file):
    """Test extracting audio from video file."""
    mock_audio = MagicMock()
    mock_audio.set_frame_rate.return_value = mock_audio
    mock_audio.set_channels.return_value = mock_audio
    
    with patch('src.utils.video_utils.AudioSegment') as mock_segment:
        mock_segment.from_file.return_value = mock_audio
        
        result = extract_audio_from_video(sample_video_file, target_rate=16000)
        
        # Verify AudioSegment.from_file was called with video path
        mock_segment.from_file.assert_called_once_with(sample_video_file)
        mock_audio.set_frame_rate.assert_called_once_with(16000)
        mock_audio.set_channels.assert_called_once_with(1)
        mock_audio.export.assert_called_once()


@pytest.mark.unit
def test_extract_audio_custom_rate(sample_video_file):
    """Test extracting audio with custom sample rate."""
    mock_audio = MagicMock()
    mock_audio.set_frame_rate.return_value = mock_audio
    mock_audio.set_channels.return_value = mock_audio
    
    with patch('src.utils.video_utils.AudioSegment') as mock_segment:
        mock_segment.from_file.return_value = mock_audio
        
        result = extract_audio_from_video(sample_video_file, target_rate=22050)
        
        mock_audio.set_frame_rate.assert_called_once_with(22050)

