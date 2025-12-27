import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.database_service import DatabaseService
from src.api.routes.upload import pipeline_store

router = APIRouter()


@router.get("/status/{meeting_id}")
async def get_status(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get processing status for a meeting (supports both UUID and legacy meeting_id)."""
    # Try to parse as UUID first
    try:
        meeting_uuid = uuid.UUID(meeting_id)
    except ValueError:
        # Legacy meeting_id format - use in-memory store
        status = pipeline_store.get_status(meeting_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Meeting not found")

        progress = pipeline_store.get_progress(meeting_id)
        stage = pipeline_store.get_stage(meeting_id)

        return {
            "meeting_id": meeting_id,
            "status": status,
            "progress": progress,
            "stage": stage,
            "estimated_time_remaining": None,
        }

    # Load from database
    db_service = DatabaseService(db)
    meeting = await db_service.get_meeting(meeting_uuid)

    if not meeting:
        # Fallback to in-memory store (try UUID as-is)
        status = pipeline_store.get_status(meeting_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Meeting not found")

        progress = pipeline_store.get_progress(meeting_id)
        stage = pipeline_store.get_stage(meeting_id)

        return {
            "meeting_id": meeting_id,
            "status": status,
            "progress": progress,
            "stage": stage,
            "estimated_time_remaining": None,
        }

    # Extract legacy meeting_id from file_path for PipelineStore lookup
    # file_path format: "meeting_id/audio/filename.mp4"
    legacy_meeting_id = None
    if meeting.file_path:
        # Extract the folder name (meeting_id) from the path
        path_parts = meeting.file_path.split("/")
        if len(path_parts) > 0:
            legacy_meeting_id = path_parts[0]

    # Priority: PipelineStore (real-time) > Database (persisted)
    # PipelineStore has real-time updates during processing
    # Database is source of truth for completed/error states
    
    pipeline_status = None
    pipeline_progress = None
    pipeline_stage = None
    
    if legacy_meeting_id:
        pipeline_status = pipeline_store.get_status(legacy_meeting_id)
        pipeline_progress = pipeline_store.get_progress(legacy_meeting_id)
        pipeline_stage = pipeline_store.get_stage(legacy_meeting_id)
    
    # Decision logic:
    # 1. If database says "completed", always use that (PipelineStore might be cleared)
    # 2. If PipelineStore has status, use it (real-time updates during processing)
    # 3. Otherwise, use database status
    
    if meeting.status == "completed":
        # Database is source of truth for completed meetings
        status = "completed"
        progress = 100.0
        stage = "Completed"
    elif pipeline_status is not None:
        # PipelineStore has real-time status - use it during processing
        status = pipeline_status
        progress = pipeline_progress if pipeline_progress is not None else 0.0
        stage = pipeline_stage if pipeline_stage else "Processing"
    else:
        # Fall back to database status (e.g., if PipelineStore entry doesn't exist yet)
        status = meeting.status or "uploading"
        # Estimate progress based on status
        if status == "completed":
            progress = 100.0
            stage = "Completed"
        elif status == "error":
            progress = 0.0
            stage = "Error"
        elif status == "uploading":
            progress = 0.0
            stage = "Uploading"
        else:
            progress = 0.0
            stage = "Processing"

    return {
        "meeting_id": str(meeting_uuid),
        "status": status,
        "progress": progress,
        "stage": stage,
        "estimated_time_remaining": None,
    }

