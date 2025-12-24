from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.transcription_service import TranscriptionResult


class TranscriptStore:
    """
    Simple filesystem-backed transcript store for pipeline prototyping.
    Persistence to DB is deferred to the FAISS/DB phase.
    """

    def __init__(self, base_path: Path = Path("storage")) -> None:
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_transcript(self, meeting_id: str, transcript: "TranscriptionResult") -> Path:
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
        
        # Also save diarized transcript as readable text
        self.save_diarized_transcript(meeting_id, transcript)
        
        return transcript_path

    def save_diarized_transcript(self, meeting_id: str, transcript: "TranscriptionResult") -> Path:
        """Save a human-readable diarized transcript with speaker labels."""
        meeting_dir = self.base_path / meeting_id
        meeting_dir.mkdir(parents=True, exist_ok=True)
        diarized_path = meeting_dir / "diarized_transcript.txt"
        
        lines = []
        current_speaker = None
        
        for seg in transcript.segments:
            speaker = seg.speaker or "Unknown"
            timestamp = f"[{self._format_time(seg.start)} - {self._format_time(seg.end)}]"
            
            # Add speaker header if speaker changed
            if speaker != current_speaker:
                if lines:  # Add blank line between speakers
                    lines.append("")
                lines.append(f"{speaker} {timestamp}:")
                current_speaker = speaker
            
            # Add the text (indented)
            lines.append(f"  {seg.text}")
        
        content = "\n".join(lines)
        with diarized_path.open("w", encoding="utf-8") as f:
            f.write(content)
        
        return diarized_path
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def load_transcript(self, meeting_id: str) -> Optional[dict]:
        transcript_path = self.base_path / meeting_id / "transcript.json"
        if not transcript_path.exists():
            return None
        with transcript_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    
    def load_diarized_transcript(self, meeting_id: str) -> Optional[str]:
        """Load the human-readable diarized transcript."""
        diarized_path = self.base_path / meeting_id / "diarized_transcript.txt"
        if not diarized_path.exists():
            return None
        with diarized_path.open("r", encoding="utf-8") as f:
            return f.read()

