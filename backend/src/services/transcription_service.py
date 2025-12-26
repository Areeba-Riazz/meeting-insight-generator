from __future__ import annotations


# CRITICAL: Patch torch.load BEFORE any imports
import torch
_original_torch_load = torch.load
def force_weights_only_false(f, *args, **kwargs):
    kwargs['weights_only'] = False
    return _original_torch_load(f, *args, **kwargs)
torch.load = force_weights_only_false

# Now your normal imports
from pathlib import Path
from typing import Optional, Callable
import whisperx
# ... rest of your imports


import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from src.utils.audio_utils import preprocess_audio

if TYPE_CHECKING:
    from src.services.transcript_store import TranscriptStore


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
    Transcription service using WhisperX for better accuracy and speaker diarization.
    WhisperX provides:
    - Accurate word-level timestamps
    - Integrated speaker diarization
    - Better alignment than vanilla Whisper
    """

    def __init__(
        self,
        model_name: str = "medium",
        device: str = "cpu",
        diarization_enabled: bool = True,
        diarization_token: Optional[str] = None,
        transcript_store: "Optional[TranscriptStore]" = None,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.diarization_enabled = diarization_enabled
        self.diarization_token = diarization_token or os.getenv("HUGGINGFACE_TOKEN")
        self._model = None
        self.transcript_store = transcript_store
        self._use_whisperx = True  # Try WhisperX first, fall back to vanilla if not available

    def _load_whisperx_model(self):
        """Load WhisperX model for transcription and alignment."""
        if self._model is None:
            try:
                import whisperx
                import torch
                
                # Fix for PyTorch 2.6+ weights_only=True default
                # Add safe globals for omegaconf which WhisperX uses
                try:
                    from omegaconf import DictConfig, ListConfig
                    torch.serialization.add_safe_globals([DictConfig, ListConfig])
                    print("[TranscriptionService] Added omegaconf to safe globals for PyTorch 2.6+")
                except ImportError:
                    pass  # omegaconf might not be installed yet
                
                print(f"[TranscriptionService] Loading WhisperX model: {self.model_name}")
                self._model = whisperx.load_model(
                    self.model_name, 
                    self.device, 
                    compute_type="float32" if self.device == "cpu" else "float16"
                )
                print(f"[TranscriptionService] WhisperX model loaded successfully")
                self._use_whisperx = True
            except ImportError:
                print("[TranscriptionService] WhisperX not installed, falling back to vanilla Whisper")
                print("[TranscriptionService] To enable WhisperX: pip install whisperx")
                self._use_whisperx = False
                import whisper
                self._model = whisper.load_model(self.model_name, device=self.device)
            except Exception as e:
                print(f"[TranscriptionService] Error loading WhisperX: {e}")
                print("[TranscriptionService] Falling back to vanilla Whisper")
                self._use_whisperx = False
                import whisper
                self._model = whisper.load_model(self.model_name, device=self.device)
        return self._model

    def transcribe(
        self,
        audio_path: Path,
        meeting_id: Optional[str] = None,
        on_status: Optional[Callable[[str, Optional[float], Optional[str]], None]] = None,
    ) -> TranscriptionResult:
        """
        Run the transcription pipeline with WhisperX for better accuracy and diarization.
        """

        def notify(status: str, progress: Optional[float] = None, stage_desc: Optional[str] = None) -> None:
            if on_status:
                try:
                    on_status(status, progress, stage_desc)
                    print(f"[TranscriptionService] Status: {status}, Progress: {progress}%, Stage: {stage_desc}")
                except Exception as e:
                    print(f"[TranscriptionService] Failed to update status: {e}")
                    pass

        import time

        notify("loading_model", 10, "Loading WhisperX model")
        time.sleep(0.5)
        model = self._load_whisperx_model()

        notify("extracting_audio", 20, "Extracting and preprocessing audio")
        time.sleep(0.5)
        preprocessed_path = preprocess_audio(audio_path)

        if self._use_whisperx:
            # Use WhisperX pipeline
            result = self._transcribe_with_whisperx(preprocessed_path, notify)
        else:
            # Fallback to vanilla Whisper
            result = self._transcribe_with_vanilla_whisper(preprocessed_path, model, notify)

        notify("saving_transcript", 75, "Saving transcript")
        time.sleep(0.5)
        if self.transcript_store and meeting_id:
            self.transcript_store.save_transcript(meeting_id, result)

        return result

    def _transcribe_with_whisperx(
        self,
        audio_path: Path,
        notify: Callable[[str, Optional[float], Optional[str]], None],
    ) -> TranscriptionResult:
        """Transcribe using WhisperX with alignment and diarization."""
        import whisperx
        import time

        # Step 1: Transcribe
        notify("transcribing", 35, "Transcribing audio with WhisperX")
        time.sleep(0.5)
        audio = whisperx.load_audio(str(audio_path))
        result = self._model.transcribe(audio, batch_size=16)
        
        # Step 2: Align for better timestamps
        notify("transcribing", 45, "Aligning timestamps")
        time.sleep(0.5)
        alignment_successful = False
        try:
            model_a, metadata = whisperx.load_align_model(
                language_code=result["language"], 
                device=self.device
            )
            result = whisperx.align(
                result["segments"], 
                model_a, 
                metadata, 
                audio, 
                self.device, 
                return_char_alignments=False
            )
            alignment_successful = True
            print(f"[TranscriptionService] Alignment completed for language: {result.get('language', 'unknown')}")
            
            # DEBUG: Check result structure
            print(f"[DEBUG] Alignment result keys: {list(result.keys())}")
            if 'segments' in result and len(result['segments']) > 0:
                print(f"[DEBUG] First segment keys: {list(result['segments'][0].keys())}")
                print(f"[DEBUG] First segment has 'words': {'words' in result['segments'][0]}")
            
        except Exception as e:
            print(f"[TranscriptionService] Alignment failed: {e}, continuing without alignment")

        # Step 3: Diarize (assign speakers) - UPDATED FOR WHISPERX 3.7+
        segments_with_speakers = []
        # Step 3: Diarize (assign speakers) - UPDATED FOR WHISPERX 3.7+
        segments_with_speakers = []
        if self.diarization_enabled and self.diarization_token and alignment_successful:
            notify("diarizing", 60, "Identifying speakers with pyannote")
            time.sleep(0.5)
            try:
                # WhisperX 3.7+ uses pyannote.audio.Pipeline directly
                from pyannote.audio import Pipeline
                import pandas as pd
                
                print(f"[TranscriptionService] Loading diarization pipeline (pyannote)...")
                
                diarize_model = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=self.diarization_token
                )
                
                # Run diarization - pass the audio file path
                print(f"[TranscriptionService] Running speaker diarization...")
                diarize_segments = diarize_model(str(audio_path))
                
                print(f"[TranscriptionService] Assigning speakers to words...")
                
                # Convert pyannote Annotation to list format for whisperx
                diarize_list = []
                for turn, _, speaker in diarize_segments.itertracks(yield_label=True):
                    diarize_list.append({
                        'segment': {'start': turn.start, 'end': turn.end},
                        'label': speaker
                    })
                
                print(f"[DEBUG] Diarization found {len(diarize_list)} speaker segments")
                
                if len(diarize_list) == 0:
                    print(f"[TranscriptionService] Warning: No speakers detected by diarization!")
                    result_with_speakers = result
                else:
                    # Create DataFrame for whisperx compatibility
                    diarize_df = pd.DataFrame([{
                        'start': item['segment']['start'],
                        'end': item['segment']['end'],
                        'speaker': item['label']
                    } for item in diarize_list])
                    
                    print(f"[DEBUG] Diarization DataFrame shape: {diarize_df.shape}")
                    print(f"[DEBUG] Unique speakers: {diarize_df['speaker'].unique()}")
                    
                    # Manually assign speakers to segments based on overlap
                    for seg in result.get("segments", []):
                        seg_start = seg.get('start', 0)
                        seg_end = seg.get('end', 0)
                        seg_mid = (seg_start + seg_end) / 2
                        
                        # Find speaker with maximum overlap
                        best_speaker = None
                        max_overlap = 0
                        
                        for _, row in diarize_df.iterrows():
                            overlap_start = max(seg_start, row['start'])
                            overlap_end = min(seg_end, row['end'])
                            overlap = max(0, overlap_end - overlap_start)
                            
                            if overlap > max_overlap:
                                max_overlap = overlap
                                best_speaker = row['speaker']
                        
                        seg['speaker'] = best_speaker
                    
                    result_with_speakers = result
                
                # Count unique speakers
                speakers = set()
                for seg in result_with_speakers.get("segments", []):
                    if seg.get("speaker"):
                        speakers.add(seg["speaker"])
                print(f"[TranscriptionService] Identified {len(speakers)} unique speakers: {speakers}")
                
                # Convert to our format
                for seg in result_with_speakers.get("segments", []):
                    segments_with_speakers.append(
                        TranscriptionSegment(
                            text=seg.get("text", "").strip(),
                            start=seg.get("start", 0.0),
                            end=seg.get("end", 0.0),
                            speaker=seg.get("speaker"),
                        )
                    )
                
                labeled_count = sum(1 for s in segments_with_speakers if s.speaker is not None)
                print(f"[TranscriptionService] Assigned speaker labels to {labeled_count}/{len(segments_with_speakers)} segments")
                
            except KeyError as e:
                print(f"[TranscriptionService] Diarization KeyError: {e}")
                import traceback
                print(traceback.format_exc())
                print(f"[TranscriptionService] Falling back to segments without speaker labels")
                # Fall back to segments without speakers
                for seg in result.get("segments", []):
                    segments_with_speakers.append(
                        TranscriptionSegment(
                            text=seg.get("text", "").strip(),
                            start=seg.get("start", 0.0),
                            end=seg.get("end", 0.0),
                            speaker=None,
                        )
                    )
            except Exception as e:
                print(f"[TranscriptionService] Diarization failed: {e}")
                import traceback
                print(traceback.format_exc())
                # Fall back to segments without speakers
                for seg in result.get("segments", []):
                    segments_with_speakers.append(
                        TranscriptionSegment(
                            text=seg.get("text", "").strip(),
                            start=seg.get("start", 0.0),
                            end=seg.get("end", 0.0),
                            speaker=None,
                        )
                    )


        # Build full text from segments
        full_text = " ".join(seg.text for seg in segments_with_speakers if seg.text)

        return TranscriptionResult(
            text=full_text,
            segments=segments_with_speakers,
            model=f"whisperx-{self.model_name}",
        )
    
    def _transcribe_with_vanilla_whisper(
        self,
        audio_path: Path,
        model: Any,
        notify: Callable[[str, Optional[float], Optional[str]], None],
    ) -> TranscriptionResult:
        """Fallback transcription using vanilla Whisper (no diarization)."""
        import time
        
        notify("transcribing", 40, "Transcribing audio with Whisper")
        result: Dict[str, Any] = model.transcribe(str(audio_path))

        notify("diarizing", 60, "Processing segments")
        time.sleep(0.5)
        
        segments = [
            TranscriptionSegment(
                text=seg.get("text", "").strip(),
                start=seg.get("start", 0.0),
                end=seg.get("end", 0.0),
                speaker=None,
            )
            for seg in result.get("segments", [])
        ]

        return TranscriptionResult(
            text=result.get("text", "").strip(),
            segments=segments,
            model=self.model_name,
        )
