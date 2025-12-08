import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from backend.src.agents.action_item_agent import ActionItemAgent
from backend.src.agents.decision_agent import DecisionAgent
from backend.src.agents.sentiment_agent import SentimentAgent
from backend.src.agents.summary_agent import SummaryAgent
from backend.src.agents.topic_agent import TopicAgent
from backend.src.utils.validation import validate_file
from backend.src.services.agent_orchestrator import AgentOrchestrator
from backend.src.services.pipeline_store import PipelineStore
from backend.src.services.transcript_store import TranscriptStore
from backend.src.services.transcription_service import TranscriptionService

router = APIRouter()

pipeline_store = PipelineStore()
transcript_store = TranscriptStore(base_path=Path("backend/storage"))
transcription_service = TranscriptionService(
    model_name="medium",
    device="cpu",
    diarization_enabled=False,
    transcript_store=transcript_store,
)
agents = [
    TopicAgent(),
    DecisionAgent(),
    ActionItemAgent(),
    SentimentAgent(),
    SummaryAgent(),
]
orchestrator = AgentOrchestrator(transcription_service=transcription_service, agents=agents)


async def process_meeting(meeting_id: str, audio_path: Path) -> None:
    try:
        pipeline_store.set_status(meeting_id, "processing")
        result = await orchestrator.process(meeting_id, audio_path)
        pipeline_store.set_result(meeting_id, result)
        pipeline_store.set_status(meeting_id, "completed")
    except Exception as e:  # pragma: no cover - basic error propagation
        pipeline_store.set_status(meeting_id, f"error: {e}")


@router.post("/upload")
async def upload_meeting_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Save uploaded file to meeting-specific folder
    meeting_id = str(uuid.uuid4())
    meeting_dir = Path("backend/storage") / meeting_id / "audio"
    meeting_dir.mkdir(parents=True, exist_ok=True)
    audio_path = meeting_dir / file.filename

    content = await file.read()
    with audio_path.open("wb") as f:
        f.write(content)

    # Validate file type/size
    try:
        validate_file(audio_path, content_type=file.content_type, max_mb=500)
    except ValueError as e:
        audio_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))

    pipeline_store.set_status(meeting_id, "queued")
    background_tasks.add_task(process_meeting, meeting_id, audio_path)

    return {"meeting_id": meeting_id, "status": "queued"}

