"""Unit tests for validation utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.validation import validate_file, ALLOWED_AUDIO_TYPES, ALLOWED_VIDEO_TYPES


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    test_file = tmp_path / "test_file.wav"
    test_file.write_bytes(b"fake audio content" * 1000)  # ~17KB
    return test_file


@pytest.mark.unit
def test_validate_file_size_too_large_using_mock(tmp_path):
    """Test validation fails for file that's too large."""
    # Note: WindowsPath.stat() is read-only and cannot be patched directly.
    # This test is skipped on Windows. File size validation is tested through
    # integration tests and other validation paths.
    import platform
    if platform.system() == "Windows":
        pytest.skip("Cannot mock Path.stat() on Windows - tested via integration tests")
    
    test_file = tmp_path / "large_file.wav"
    test_file.write_bytes(b"test")
    
    # Create a mock stat result with large size
    mock_stat_result = MagicMock()
    mock_stat_result.st_size = 600 * 1024 * 1024  # 600MB
    
    # Patch Path.stat at the module level
    with patch.object(Path, 'stat', return_value=mock_stat_result):
        with patch('src.utils.validation.Path.stat', return_value=mock_stat_result):
            with pytest.raises(ValueError, match="too large"):
                validate_file(test_file, "audio/wav", max_mb=500)


@pytest.mark.unit
def test_validate_file_custom_max_size_using_mock(tmp_path):
    """Test validation with custom max_mb parameter."""
    # Note: WindowsPath.stat() is read-only and cannot be patched directly.
    # This test is skipped on Windows. File size validation is tested through
    # integration tests and other validation paths.
    import platform
    if platform.system() == "Windows":
        pytest.skip("Cannot mock Path.stat() on Windows - tested via integration tests")
    
    test_file = tmp_path / "test_file.wav"
    test_file.write_bytes(b"test")
    
    # Create a mock stat result with 100MB size
    mock_stat_result = MagicMock()
    mock_stat_result.st_size = 100 * 1024 * 1024  # 100MB
    
    # Patch Path.stat at the module level
    with patch.object(Path, 'stat', return_value=mock_stat_result):
        with patch('src.utils.validation.Path.stat', return_value=mock_stat_result):
            # Should pass with max_mb=200
            validate_file(test_file, "audio/wav", max_mb=200)
            
            # Should fail with max_mb=50 (same 100MB file)
            with pytest.raises(ValueError, match="too large"):
                validate_file(test_file, "audio/wav", max_mb=50)


@pytest.mark.unit
def test_validate_file_audio_valid(temp_file):
    """Test validation of valid audio file."""
    # Should not raise
    validate_file(temp_file, "audio/wav")
    validate_file(temp_file, "audio/mpeg")
    validate_file(temp_file, "audio/mp3")


@pytest.mark.unit
def test_validate_file_video_valid(temp_file):
    """Test validation of valid video file."""
    # Should not raise
    validate_file(temp_file, "video/mp4")
    validate_file(temp_file, "video/x-matroska")
    validate_file(temp_file, "video/quicktime")




@pytest.mark.unit
def test_validate_file_invalid_type(temp_file):
    """Test validation fails for unsupported file type."""
    with pytest.raises(ValueError, match="Unsupported file type"):
        validate_file(temp_file, "application/pdf")
    
    with pytest.raises(ValueError, match="Unsupported file type"):
        validate_file(temp_file, "text/plain")


@pytest.mark.unit
def test_validate_file_guessed_type(temp_file):
    """Test validation uses mimetypes.guess_type when content_type is None."""
    with patch('src.utils.validation.mimetypes.guess_type', return_value=('audio/wav', None)):
        # Should not raise when guessed type is valid
        validate_file(temp_file, None)


@pytest.mark.unit
def test_validate_file_guessed_type_invalid(temp_file):
    """Test validation fails when guessed type is invalid."""
    with patch('src.utils.validation.mimetypes.guess_type', return_value=('text/plain', None)):
        with pytest.raises(ValueError, match="Unsupported file type"):
            validate_file(temp_file, None)


@pytest.mark.unit
def test_validate_file_no_type(temp_file):
    """Test validation fails when no type can be determined."""
    with patch('src.utils.validation.mimetypes.guess_type', return_value=(None, None)):
        with pytest.raises(ValueError, match="Unsupported file type"):
            validate_file(temp_file, None)




@pytest.mark.unit
def test_validate_file_all_allowed_audio_types(temp_file):
    """Test all allowed audio types are accepted."""
    for audio_type in ALLOWED_AUDIO_TYPES:
        try:
            validate_file(temp_file, audio_type)
        except ValueError:
            pytest.fail(f"Audio type {audio_type} should be allowed")


@pytest.mark.unit
def test_validate_file_all_allowed_video_types(temp_file):
    """Test all allowed video types are accepted."""
    for video_type in ALLOWED_VIDEO_TYPES:
        try:
            validate_file(temp_file, video_type)
        except ValueError:
            pytest.fail(f"Video type {video_type} should be allowed")


@pytest.mark.unit
def test_validate_file_audio_prefix_matching(temp_file):
    """Test that audio types starting with 'audio/' are checked."""
    # content_type starts with "audio/" but not in ALLOWED_AUDIO_TYPES
    with pytest.raises(ValueError, match="Unsupported file type"):
        validate_file(temp_file, "audio/ogg")


@pytest.mark.unit
def test_validate_file_video_prefix_matching(temp_file):
    """Test that video types starting with 'video/' are checked."""
    # content_type starts with "video/" but not in ALLOWED_VIDEO_TYPES
    with pytest.raises(ValueError, match="Unsupported file type"):
        validate_file(temp_file, "video/avi")

