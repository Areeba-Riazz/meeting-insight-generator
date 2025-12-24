from __future__ import annotations

import tempfile
from pathlib import Path

from pydub import AudioSegment
from src.utils.video_utils import extract_audio_from_video


def preprocess_audio(audio_path: Path, target_rate: int = 16000) -> Path:
    """
    Normalize, convert to mono, and resample audio to a temporary WAV file.
    Returns the path to the preprocessed file.
    """
    # If this is a video file, extract audio first
    if audio_path.suffix.lower() in {".mp4", ".mkv", ".mov"}:
        audio_path = extract_audio_from_video(audio_path, target_rate=target_rate)

    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_frame_rate(target_rate).set_channels(1)
    temp_dir = Path(tempfile.gettempdir())
    out_path = temp_dir / f"preprocessed_{audio_path.stem}.wav"
    audio.export(out_path, format="wav")
    return out_path

