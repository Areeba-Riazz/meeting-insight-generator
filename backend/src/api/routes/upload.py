import os
import uuid
import json
import re
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from src.utils.validation import validate_file
from src.services.pipeline_store import PipelineStore

# Load environment variables from .env file
load_dotenv()
from src.services.transcript_store import TranscriptStore
from src.services.transcription_service import TranscriptionService
from src.services.agent_orchestrator import AgentOrchestrator
from src.agents.summary_agent import SummaryAgent
from src.agents.topic_agent import TopicAgent
from src.agents.decision_agent import DecisionAgent
from src.agents.action_item_agent import ActionItemAgent
from src.agents.sentiment_agent import SentimentAgent
from src.agents.config import AgentSettings

router = APIRouter()

pipeline_store = PipelineStore()
transcript_store = TranscriptStore(base_path=Path("storage"))
transcription_service = TranscriptionService(
    model_name="small",
    device="cpu",
    diarization_enabled=True,
    diarization_token=os.getenv("HUGGINGFACE_TOKEN"),
    transcript_store=transcript_store,
)


def sanitize_filename(filename: str, max_length: int = 50) -> str:
    """
    Sanitize filename by removing/replacing special characters.
    
    Args:
        filename: Original filename (without extension)
        max_length: Maximum length for sanitized name
        
    Returns:
        Sanitized filename safe for use in folder names
    """
    # Remove or replace special characters
    sanitized = re.sub(r'[^\w\s-]', '', filename)
    # Replace spaces and underscores with hyphens
    sanitized = re.sub(r'[\s_]+', '_', sanitized)
    # Remove leading/trailing hyphens and underscores
    sanitized = sanitized.strip('-_')
    # Convert to lowercase
    sanitized = sanitized.lower()
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('-_')
    # Ensure we have something left
    if not sanitized:
        sanitized = "meeting"
    return sanitized


def generate_meeting_id(filename: str) -> tuple[str, str]:
    """
    Generate a unique meeting ID based on filename and timestamp.
    
    Args:
        filename: Original filename with extension
        
    Returns:
        Tuple of (meeting_id, uuid) where meeting_id is the folder name
    """
    # Extract filename without extension
    name_without_ext = Path(filename).stem
    
    # Sanitize the filename
    sanitized_name = sanitize_filename(name_without_ext)
    
    # Generate timestamp in readable format
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Generate UUID for internal tracking
    meeting_uuid = str(uuid.uuid4())
    
    # Create meeting ID
    meeting_id = f"{sanitized_name}_{timestamp}"
    
    # Ensure uniqueness by checking if folder exists
    counter = 1
    original_meeting_id = meeting_id
    storage_path = Path("storage")
    while (storage_path / meeting_id).exists():
        meeting_id = f"{original_meeting_id}_{counter}"
        counter += 1
    
    return meeting_id, meeting_uuid


def create_metadata_file(
    meeting_dir: Path,
    meeting_uuid: str,
    original_filename: str,
    folder_name: str,
    file_size: int,
    content_type: str | None
) -> None:
    """
    Create metadata.json file in the meeting folder.
    
    Args:
        meeting_dir: Path to meeting directory
        meeting_uuid: UUID for internal tracking
        original_filename: Original uploaded filename
        folder_name: Generated folder name
        file_size: Size of uploaded file in bytes
        content_type: MIME type of uploaded file
    """
    metadata = {
        "uuid": meeting_uuid,
        "meeting_name": Path(original_filename).stem,
        "folder_name": folder_name,
        "upload_timestamp": datetime.now().isoformat(),
        "file_info": {
            "original_filename": original_filename,
            "size_bytes": file_size,
            "content_type": content_type
        }
    }
    
    metadata_path = meeting_dir / "metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

async def process_meeting(meeting_id: str, audio_path: Path) -> None:
    try:
        pipeline_store.set_status(meeting_id, "processing", progress=5, stage="Initializing")

        def update_status(stage: str, progress: float = None, stage_desc: str = None) -> None:
            pipeline_store.set_status(meeting_id, stage, progress=progress, stage=stage_desc)

        # Initialize agents
        agent_settings = AgentSettings()
        agents = [
            SummaryAgent(),
            TopicAgent(),
            DecisionAgent(),
            ActionItemAgent(),
            SentimentAgent(),
        ]
        
        # Create orchestrator - it handles both transcription and AI agents
        orchestrator = AgentOrchestrator(
            transcription_service=transcription_service,
            agents=agents
        )
        
        # Run full pipeline (transcription + AI agents) with real-time status updates
        results = await orchestrator.process(meeting_id, audio_path, on_status=update_status)
        
        # Step 3: Save results (transcript + agent insights)
        update_status("saving_results", progress=95, stage_desc="Saving results")
        pipeline_store.set_result(meeting_id, results)
        pipeline_store.set_status(meeting_id, "completed", progress=100, stage="Completed")
    except Exception as e:  # pragma: no cover - basic error propagation
        pipeline_store.set_status(meeting_id, f"error: {e}", progress=0, stage="Error")
    finally:
        pipeline_store.release_processing()


@router.post("/upload")
async def upload_meeting_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Check if already processing - reject if so (sequential processing only)
    if pipeline_store.is_processing():
        raise HTTPException(
            status_code=409,
            detail="Another file is currently being processed. Please wait for it to complete."
        )

    # Generate meeting ID from filename and timestamp
    meeting_id, meeting_uuid = generate_meeting_id(file.filename)
    meeting_dir = Path("storage") / meeting_id / "audio"
    meeting_dir.mkdir(parents=True, exist_ok=True)
    audio_path = meeting_dir / file.filename

    content = await file.read()
    with audio_path.open("wb") as f:
        f.write(content)
    
    # Create metadata.json file
    create_metadata_file(
        meeting_dir=meeting_dir.parent,
        meeting_uuid=meeting_uuid,
        original_filename=file.filename,
        folder_name=meeting_id,
        file_size=len(content),
        content_type=file.content_type
    )

    # Validate file type/size
    try:
        validate_file(audio_path, content_type=file.content_type, max_mb=500)
    except ValueError as e:
        audio_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))

    # Acquire processing lock
    acquired = pipeline_store.acquire_processing()
    if not acquired:
        audio_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=409,
            detail="Another file is currently being processed. Please wait for it to complete."
        )

    pipeline_store.set_status(meeting_id, "queued", progress=0, stage="Queued")
    background_tasks.add_task(process_meeting, meeting_id, audio_path)

    return {"meeting_id": meeting_id, "status": "queued"}

