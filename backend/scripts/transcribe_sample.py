from pathlib import Path

from src.services.transcription_service import TranscriptionService
from src.services.transcript_store import TranscriptStore


def main() -> None:
    audio_path = Path("storage/sample_audio/meeting.mp3")
    if not audio_path.exists():
        raise FileNotFoundError(f"Sample audio not found at {audio_path}")

    store = TranscriptStore(base_path=Path("storage"))
    svc = TranscriptionService(
        model_name="medium",
        device="cpu",
        diarization_enabled=False,
    )
    result = svc.transcribe(audio_path, meeting_id="sample")
    print("Full text (first 500 chars):")
    print(result.text[:500])
    print("\nFirst 3 segments:")
    for seg in result.segments[:3]:
        print(seg)
    print("\nSaved transcript at:", store.base_path / "sample" / "transcript.json")


if __name__ == "__main__":
    main()

