from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.src.utils.audio_utils import preprocess_audio
from backend.src.services.transcript_store import TranscriptStore


@dataclass
class TranscriptionSegment:
    text: str
    start: float
    end: float
    speaker: Optional[str] = None


@dataclass
class TranscriptionResult:
    text: str
    segments: List[TranscriptionSegment]
    model: str


class TranscriptionService:
    """
    Pipeline-first transcription service.
    - Uses Whisper for ASR.
    - Optional diarization hook (to be wired later).
    - In-memory outputs (persistence deferred to the FAISS/DB phase).
    """

    def __init__(
        self,
        model_name: str = "medium",
        device: str = "cpu",
        diarization_enabled: bool = False,
        diarization_token: Optional[str] = None,
        transcript_store: Optional[TranscriptStore] = None,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.diarization_enabled = diarization_enabled
        self.diarization_token = diarization_token
        self._model = None
        self._diarization_pipeline = None
        self.transcript_store = transcript_store

    def _load_model(self):
        if self._model is None:
            import whisper

            self._model = whisper.load_model(self.model_name, device=self.device)
        return self._model

    def _load_diarization(self):
        if not self.diarization_enabled:
            return None
        if self._diarization_pipeline is None:
            try:
                from pyannote.audio import Pipeline
            except ImportError:
                return None
            if not self.diarization_token:
                return None
            self._diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.diarization_token,
            )
        return self._diarization_pipeline

    def _apply_diarization(
        self, audio_path: Path, whisper_segments: List[Dict[str, Any]]
    ) -> List[TranscriptionSegment]:
        pipeline = self._load_diarization()
        if pipeline is None:
            return [
                TranscriptionSegment(
                    text=seg.get("text", "").strip(),
                    start=seg.get("start", 0.0),
                    end=seg.get("end", 0.0),
                    speaker=None,
                )
                for seg in whisper_segments
            ]

        diarization = pipeline(str(audio_path))
        speaker_timeline: List[Tuple[Tuple[float, float], str]] = [
            ((turn.start, turn.end), speaker) for turn, _, speaker in diarization.itertracks(yield_label=True)
        ]

        def find_speaker(start: float, end: float) -> Optional[str]:
            mid = (start + end) / 2.0
            for (s, e), spk in speaker_timeline:
                if s <= mid <= e:
                    return spk
            return None

        return [
            TranscriptionSegment(
                text=seg.get("text", "").strip(),
                start=seg.get("start", 0.0),
                end=seg.get("end", 0.0),
                speaker=find_speaker(seg.get("start", 0.0), seg.get("end", 0.0)),
            )
            for seg in whisper_segments
        ]

    def transcribe(self, audio_path: Path, meeting_id: Optional[str] = None) -> TranscriptionResult:
        # Preprocess audio (normalize, resample, mono)
        preprocessed_path = preprocess_audio(audio_path)

        model = self._load_model()
        result: Dict[str, Any] = model.transcribe(str(preprocessed_path))

        # Apply diarization (optional)
        segments = self._apply_diarization(preprocessed_path, result.get("segments", []))

        transcription = TranscriptionResult(
            text=result.get("text", "").strip(),
            segments=segments,
            model=self.model_name,
        )

        # Store transcript if a store is provided (still filesystem/in-memory, DB deferred)
        if self.transcript_store and meeting_id:
            self.transcript_store.save_transcript(meeting_id, transcription)

        return transcription

