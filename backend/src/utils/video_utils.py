from __future__ import annotations

import tempfile
from pathlib import Path

from pydub import AudioSegment


def extract_audio_from_video(video_path: Path, target_rate: int = 16000) -> Path:
    """
    Extract audio track from a video file to a temporary WAV.
    Requires ffmpeg to be installed.
    """
    audio = AudioSegment.from_file(video_path)
    audio = audio.set_frame_rate(target_rate).set_channels(1)
    temp_dir = Path(tempfile.gettempdir())
    out_path = temp_dir / f"extracted_{video_path.stem}.wav"
    audio.export(out_path, format="wav")
    return out_path

