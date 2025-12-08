from __future__ import annotations

import mimetypes
from pathlib import Path

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/aac",
    "audio/m4a",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/x-matroska",
    "video/quicktime",
}


def validate_file(path: Path, content_type: str | None, max_mb: int = 500) -> None:
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_mb:
        raise ValueError(f"File too large ({size_mb:.1f}MB > {max_mb}MB limit)")

    guessed_type, _ = mimetypes.guess_type(path.name)
    ctype = content_type or guessed_type or ""

    if ctype.startswith("audio/") and ctype in ALLOWED_AUDIO_TYPES:
        return
    if ctype.startswith("video/") and ctype in ALLOWED_VIDEO_TYPES:
        return

    raise ValueError(f"Unsupported file type: {ctype}")

