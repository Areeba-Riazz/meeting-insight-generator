import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.action_item_agent import ActionItemAgent
from src.agents.config import AgentSettings
from src.agents.decision_agent import DecisionAgent
from src.agents.sentiment_agent import SentimentAgent
from src.agents.summary_agent import SummaryAgent
from src.agents.topic_agent import TopicAgent
from src.core.database import get_db
from src.services.agent_orchestrator import AgentOrchestrator
from src.services.database_service import DatabaseService
from src.services.pipeline_store import PipelineStore
from src.services.transcript_store import TranscriptStore
from src.services.transcription_service import TranscriptionService
from src.services.vector_store_service import VectorStoreService
from src.utils.error_handlers import handle_connection_errors
from src.utils.validation import validate_file

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

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
vector_store = VectorStoreService(
    vector_store_path=Path("storage/vectors"),
    embedding_model_name=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
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
    meeting_uuid: str | uuid.UUID,
    original_filename: str,
    folder_name: str,
    file_size: int,
    content_type: str | None
) -> None:
    """
    Create metadata.json file in the meeting folder.
    
    Args:
        meeting_dir: Path to meeting directory
        meeting_uuid: UUID for internal tracking (can be UUID object or string)
        original_filename: Original uploaded filename
        folder_name: Generated folder name
        file_size: Size of uploaded file in bytes
        content_type: MIME type of uploaded file
    """
    # Convert UUID to string if needed
    uuid_str = str(meeting_uuid) if meeting_uuid else None
    
    metadata = {
        "uuid": uuid_str,
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
    try:
        # Write to a temporary file first, then rename (atomic write)
        temp_path = metadata_path.with_suffix('.json.tmp')
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            f.flush()  # Ensure all data is written
            os.fsync(f.fileno())  # Force write to disk
        
        # Atomic rename (works on both Windows and Unix)
        temp_path.replace(metadata_path)
        logger.info(f"[Upload] Successfully created metadata.json at {metadata_path}")
    except Exception as e:
        logger.error(f"[Upload] Failed to write metadata.json: {e}", exc_info=True)
        # Clean up temp file if it exists
        temp_path = metadata_path.with_suffix('.json.tmp')
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        raise

async def process_meeting(
    meeting_id: str,
    audio_path: Path,
    meeting_uuid: Optional[uuid.UUID] = None,
    db: Optional[AsyncSession] = None,
) -> None:
    """
    Process meeting with robust error handling and connection resilience.
    
    Handles:
    - Network timeouts during transcription
    - Agent processing failures with graceful degradation
    - File I/O errors with retry logic
    """
    try:
        # Processing starts immediately after upload completes
        pipeline_store.set_status(
            meeting_id, 
            "processing", 
            progress=0, 
            stage="Initializing processing pipeline"
        )
        logger.info(f"[Upload] Starting processing for meeting {meeting_id}")

        def update_status(stage: str, progress: float = None, stage_desc: str = None) -> None:
            try:
                pipeline_store.set_status(meeting_id, stage, progress=progress, stage=stage_desc)
            except Exception as e:
                logger.warning(f"[Upload] Error updating status: {e}")

        # Initialize agents
        try:
            agent_settings = AgentSettings()
            agents = [
                SummaryAgent(),
                TopicAgent(),
                DecisionAgent(),
                ActionItemAgent(),
                SentimentAgent(),
            ]
            logger.info(f"[Upload] Initialized {len(agents)} agents")
        except Exception as e:
            logger.error(f"[Upload] Failed to initialize agents: {e}")
            update_status("error", progress=0, stage_desc=f"Failed to initialize: {str(e)[:100]}")
            return
        
        # Create orchestrator - it handles both transcription and AI agents
        try:
            orchestrator = AgentOrchestrator(
                transcription_service=transcription_service,
                agents=agents
            )
        except Exception as e:
            logger.error(f"[Upload] Failed to create orchestrator: {e}")
            update_status("error", progress=0, stage_desc=f"Pipeline initialization failed: {str(e)[:100]}")
            return
        
        # Run full pipeline with connection error handling
        try:
            results = await asyncio.wait_for(
                orchestrator.process(meeting_id, audio_path, on_status=update_status),
                timeout=600  # 10 minute timeout for entire pipeline
            )
            logger.info(f"[Upload] Pipeline completed successfully for {meeting_id}")
        except asyncio.TimeoutError:
            logger.error(f"[Upload] Pipeline timeout for {meeting_id}")
            update_status(
                "error", 
                progress=0, 
                stage_desc="Processing timeout - operation took too long"
            )
            return
        except (ConnectionResetError, ConnectionAbortedError, ConnectionRefusedError) as e:
            logger.error(f"[Upload] Pipeline connection error for {meeting_id}: {e}")
            update_status(
                "error",
                progress=0,
                stage_desc=f"Connection lost during processing: {type(e).__name__}"
            )
            return
        except Exception as e:
            logger.error(f"[Upload] Pipeline failed for {meeting_id}: {e}", exc_info=True)
            update_status(
                "error",
                progress=0,
                stage_desc=f"Processing failed: {str(e)[:100]}"
            )
            return
        
        # Step 3: Save results with retries
        update_status("saving_results", progress=95, stage_desc="Saving results")
        
        try:
            pipeline_store.set_result(meeting_id, results)
            logger.info(f"[Upload] Saved results to pipeline store for {meeting_id}")
        except Exception as e:
            logger.warning(f"[Upload] Error saving to pipeline store: {e}")
        
        # Save insights to database if meeting_uuid and db are provided
        if meeting_uuid and db:
            try:
                db_service = DatabaseService(db)
                await db_service.save_all_insights(meeting_uuid, results)
                await db_service.update_meeting_status(meeting_uuid, "completed")
                await db.commit()  # Ensure status update is committed
                logger.info(f"[Upload] Saved insights to database and updated status for {meeting_uuid}")
            except Exception as e:
                logger.error(f"[Upload] Error saving insights to database: {e}", exc_info=True)
                # Try to rollback
                try:
                    await db.rollback()
                except Exception:
                    pass
                # Continue with file-based storage as fallback
        
        # Save insights to JSON file in storage with retries (for backward compatibility)
        meeting_dir = Path("storage") / meeting_id
        insights_file = meeting_dir / "insights.json"
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with open(insights_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
                logger.info(f"[Upload] Saved insights to {insights_file}")
                break
            except IOError as e:
                logger.warning(f"[Upload] Error saving insights (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"[Upload] Failed to save insights after {max_retries} attempts")
            except Exception as e:
                logger.error(f"[Upload] Unexpected error saving insights: {e}")
                break
        
        # Step 4: Add embeddings to vector store
        update_status("saving_results", progress=98, stage_desc="Indexing for search")
        try:
            transcript_data = results.get("transcript", {})
            topics = results.get("topics", []) or results.get("topic_agent", {}).get("topics", [])
            decisions = results.get("decisions", []) or results.get("decision_agent", {}).get("decisions", [])
            action_items = results.get("action_items", []) or results.get("action_item_agent", {}).get("action_items", [])
            summary = results.get("summary", "") or results.get("summary_agent", {}).get("summary", "")
            
            # Handle case where agents return dicts with error messages
            if isinstance(topics, str) and topics.startswith("error"):
                topics = []
            if isinstance(decisions, str) and decisions.startswith("error"):
                decisions = []
            if isinstance(action_items, str) and action_items.startswith("error"):
                action_items = []
            if isinstance(summary, str) and summary.startswith("error"):
                summary = None
            
            vectors_added = vector_store.add_meeting_embeddings(
                meeting_id=meeting_id,
                transcript=transcript_data,
                topics=topics if isinstance(topics, list) else None,
                decisions=decisions if isinstance(decisions, list) else None,
                action_items=action_items if isinstance(action_items, list) else None,
                summary=summary if summary else None,
            )
            logger.info(f"[Upload] Added {vectors_added} vectors to vector store for {meeting_id}")
        except Exception as e:
            logger.warning(f"[Upload] Error adding vectors to vector store: {e}")
            # Non-critical error - continue anyway
        
        pipeline_store.set_status(meeting_id, "completed", progress=100, stage="Completed")
        logger.info(f"[Upload] Meeting {meeting_id} processing completed")
        
    except Exception as e:  # pragma: no cover - catch-all error handling
        logger.error(f"[Upload] Unexpected error in process_meeting: {e}", exc_info=True)
        pipeline_store.set_status(
            meeting_id, 
            f"error: {type(e).__name__}", 
            progress=0, 
            stage=str(e)[:100]
        )
    finally:
        pipeline_store.release_processing()
        logger.info(f"[Upload] Released processing lock for {meeting_id}")


async def process_meeting_with_db(
    meeting_id: str,
    audio_path: Path,
    meeting_uuid: uuid.UUID,
) -> None:
    """Wrapper to process meeting with database session."""
    from src.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            await process_meeting(meeting_id, audio_path, meeting_uuid, db)
        except Exception as e:
            logger.error(f"[Upload] Error in process_meeting_with_db: {e}", exc_info=True)
            # Update meeting status to error
            try:
                db_service = DatabaseService(db)
                await db_service.update_meeting_status(meeting_uuid, "error")
                await db.commit()
            except Exception as db_error:
                logger.error(f"[Upload] Error updating meeting status: {db_error}")



@router.post("/upload")
async def upload_meeting_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_id: Optional[str] = Query(None, description="Project UUID (optional)"),
    db: Optional[AsyncSession] = Depends(get_db),
):
    """
    Upload meeting audio file with connection error handling.
    
    Handles:
    - File read/write errors with retries
    - Validation failures with cleanup
    - Graceful error responses
    """
    if not file.filename:
        logger.warning("[Upload] Upload request with no filename")
        raise HTTPException(status_code=400, detail="Filename is required")

    # Check if already processing - reject if so (sequential processing only)
    if pipeline_store.is_processing():
        logger.warning("[Upload] Rejected - another file is being processed")
        raise HTTPException(
            status_code=409,
            detail="Another file is currently being processed. Please wait for it to complete."
        )

    try:
        # Parse project_id if provided
        project_uuid = None
        if project_id:
            try:
                project_uuid = uuid.UUID(project_id)
                # Verify project exists
                if db:
                    db_service = DatabaseService(db)
                    project = await db_service.get_project(project_uuid)
                    if not project:
                        raise HTTPException(
                            status_code=404, detail=f"Project {project_id} not found"
                        )
                else:
                    logger.warning("[Upload] Database session not available, skipping project validation")
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid project_id format: {project_id}"
                )

        # Generate meeting ID from filename and timestamp
        meeting_id, meeting_uuid_str = generate_meeting_id(file.filename)
        
        # Create meeting record in database if project_id is provided
        meeting_uuid = None
        if project_uuid and db:
            try:
                db_service = DatabaseService(db)
                meeting = await db_service.create_meeting(
                    project_id=project_uuid,
                    meeting_name=Path(file.filename).stem,
                    original_filename=file.filename,
                    file_path="",  # Will be updated after file is saved
                    file_size=0,  # Will be updated after file is read
                    content_type=file.content_type,
                )
                meeting_uuid = meeting.id
                # Commit immediately so the meeting is visible to background tasks
                await db.commit()
                logger.info(f"[Upload] Created and committed meeting record in database: {meeting_uuid}")
            except Exception as e:
                logger.error(f"[Upload] Error creating meeting record: {e}", exc_info=True)
                # Try to rollback if commit failed
                try:
                    await db.rollback()
                except Exception as rollback_error:
                    logger.error(f"[Upload] Error during rollback: {rollback_error}")
                # Continue without database record (backward compatibility)
                meeting_uuid = None
        
        logger.info(f"[Upload] New upload: {meeting_id} - {file.filename}")
        
        # Set uploading status - track file operations
        pipeline_store.set_status(
            meeting_id, 
            "uploading", 
            progress=10, 
            stage="Creating meeting directory"
        )
        
        # Create directory with error handling
        try:
            meeting_dir = Path("storage") / meeting_id / "audio"
            meeting_dir.mkdir(parents=True, exist_ok=True)
            audio_path = meeting_dir / file.filename
        except OSError as e:
            logger.error(f"[Upload] Failed to create directory for {meeting_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to create storage directory"
            )

        # Read file with timeout and error handling
        pipeline_store.set_status(
            meeting_id, 
            "uploading", 
            progress=40, 
            stage="Saving video file"
        )
        
        try:
            # Use timeout to prevent hanging on large files
            content = await asyncio.wait_for(
                file.read(),
                timeout=300  # 5 minute timeout for file read
            )
            logger.info(f"[Upload] Read {len(content)} bytes for {meeting_id}")
        except asyncio.TimeoutError:
            logger.error(f"[Upload] File read timeout for {meeting_id}")
            raise HTTPException(
                status_code=408,
                detail="File upload timeout - file is too large or connection is slow"
            )
        except Exception as e:
            logger.error(f"[Upload] Error reading file for {meeting_id}: {e}")
            raise HTTPException(
                status_code=400,
                detail="Failed to read uploaded file"
            )

        # Write file with retries
        max_retries = 3
        write_success = False
        for attempt in range(max_retries):
            try:
                with audio_path.open("wb") as f:
                    f.write(content)
                write_success = True
                logger.info(f"[Upload] Wrote file to {audio_path}")
                break
            except IOError as e:
                logger.warning(
                    f"[Upload] File write error attempt {attempt + 1}/{max_retries}: {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"[Upload] Failed to write file after {max_retries} attempts")
            except Exception as e:
                logger.error(f"[Upload] Unexpected error writing file: {e}")
                break

        if not write_success:
            raise HTTPException(
                status_code=500,
                detail="Failed to save uploaded file to storage"
            )
        
        # Create metadata.json file
        pipeline_store.set_status(
            meeting_id, 
            "uploading", 
            progress=70, 
            stage="Creating metadata"
        )
        
        try:
            # Convert UUID to string if it's a UUID object
            uuid_for_metadata = str(meeting_uuid) if meeting_uuid else None
            create_metadata_file(
                meeting_dir=meeting_dir.parent,
                meeting_uuid=uuid_for_metadata,
                original_filename=file.filename,
                folder_name=meeting_id,
                file_size=len(content),
                content_type=file.content_type
            )
            logger.info(f"[Upload] Created metadata for {meeting_id}")
        except Exception as e:
            logger.error(f"[Upload] Error creating metadata for {meeting_id}: {e}", exc_info=True)
            # Non-critical - continue anyway

        # Validate file type/size
        pipeline_store.set_status(
            meeting_id, 
            "uploading", 
            progress=90, 
            stage="Validating file"
        )
        
        try:
            validate_file(audio_path, content_type=file.content_type, max_mb=500)
            logger.info(f"[Upload] File validation passed for {meeting_id}")
        except ValueError as e:
            logger.warning(f"[Upload] File validation failed for {meeting_id}: {e}")
            # Clean up invalid file
            try:
                audio_path.unlink(missing_ok=True)
            except Exception as cleanup_error:
                logger.warning(f"[Upload] Error cleaning up invalid file: {cleanup_error}")
            raise HTTPException(status_code=400, detail=str(e))

        # Acquire processing lock
        acquired = pipeline_store.acquire_processing()
        if not acquired:
            logger.warning(f"[Upload] Failed to acquire processing lock for {meeting_id}")
            try:
                audio_path.unlink(missing_ok=True)
            except Exception as cleanup_error:
                logger.warning(f"[Upload] Error cleaning up during lock failure: {cleanup_error}")
            raise HTTPException(
                status_code=409,
                detail="Another file is currently being processed. Please wait for it to complete."
            )

        # Update meeting record with file paths if database record exists
        # IMPORTANT: Commit immediately so status route can find the meeting by file_path
        if meeting_uuid and db:
            try:
                db_service = DatabaseService(db)
                relative_audio_path = str(audio_path.relative_to(Path("storage")))
                await db_service.update_meeting_paths(
                    meeting_id=meeting_uuid,
                    transcript_path=None,  # Will be set after processing
                    diarized_transcript_path=None,  # Will be set after processing
                )
                # Update file_path and file_size
                meeting = await db_service.get_meeting(meeting_uuid)
                if meeting:
                    meeting.file_path = relative_audio_path
                    meeting.file_size_bytes = len(content)
                    await db.flush()
                # Commit immediately so status route can extract legacy_meeting_id from file_path
                await db.commit()
                logger.info(f"[Upload] Updated and committed meeting record with file paths: {relative_audio_path}")
            except Exception as e:
                logger.warning(f"[Upload] Error updating meeting record: {e}")
                # Try to rollback if commit failed
                try:
                    await db.rollback()
                except Exception as rollback_error:
                    logger.error(f"[Upload] Error during rollback: {rollback_error}")

        # Upload complete - processing will start immediately in background
        pipeline_store.set_status(meeting_id, "uploading", progress=100, stage="Upload complete")
        
        # Pass database session and meeting UUID to process_meeting if available
        if meeting_uuid and db:
            # Create a new session for background task
            from src.core.database import AsyncSessionLocal
            background_tasks.add_task(
                process_meeting_with_db,
                meeting_id,
                audio_path,
                meeting_uuid,
            )
        else:
            background_tasks.add_task(process_meeting, meeting_id, audio_path)
        
        logger.info(f"[Upload] File uploaded successfully for {meeting_id}, starting background processing")
        return {
            "meeting_id": str(meeting_uuid) if meeting_uuid else meeting_id,
            "status": "uploading",
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"[Upload] Unexpected error during file upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during file upload"
        )
