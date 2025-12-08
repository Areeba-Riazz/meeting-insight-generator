from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from backend.src.services.transcription_service import TranscriptionResult


class TranscriptStore:
    """
    Simple filesystem-backed transcript store for pipeline prototyping.
    Persistence to DB is deferred to the FAISS/DB phase.
    """

    def __init__(self, base_path: Path = Path("backend/storage")) -> None:
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_transcript(self, meeting_id: str, transcript: TranscriptionResult) -> Path:
        meeting_dir = self.base_path / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)
        transcript_path = meeting_dir / "transcript.json"
        data = {
            "text": transcript.text,
            "segments": [asdict(seg) for seg in transcript.segments],
            "model": transcript.model,
        }
        with transcript_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return transcript_path

    def load_transcript(self, meeting_id: str) -> Optional[dict]:
        transcript_path = self.base_path / meeting_id / "transcript.json"
        if not transcript_path.exists():
            return None
        with transcript_path.open("r", encoding="utf-8") as f:
            return json.load(f)

