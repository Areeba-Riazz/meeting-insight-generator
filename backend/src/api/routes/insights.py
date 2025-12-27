import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.database_service import DatabaseService
from src.api.routes.upload import pipeline_store

router = APIRouter()


@router.get("/insights/{meeting_id}")
async def get_insights(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get insights for a meeting (supports both UUID and legacy meeting_id)."""
    # Try to parse as UUID first
    try:
        meeting_uuid = uuid.UUID(meeting_id)
    except ValueError:
        # Legacy meeting_id format - try in-memory store first
        result = pipeline_store.get_result(meeting_id)
        if result:
            return {
                "meeting_id": meeting_id,
                "insights": result,
                "legacy_meeting_id": meeting_id,  # Already in legacy format
            }
        raise HTTPException(
            status_code=404,
            detail="Meeting not found. Please use UUID format for database meetings.",
        )

    # Load from database
    db_service = DatabaseService(db)
    meeting = await db_service.get_meeting(meeting_uuid)
    
    if not meeting:
        # Fallback to in-memory store
        result = pipeline_store.get_result(meeting_id)
        if result:
            return {"meeting_id": meeting_id, "insights": result}
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Get all insights from database
    insights = await db_service.get_all_insights(meeting_uuid)
    
    if not insights:
        raise HTTPException(
            status_code=404, detail="Insights not found for this meeting"
        )

    # Extract legacy meeting_id from file_path for storage access
    # file_path format: "meeting_id/audio/filename.mp4" (or "meeting_id\audio\filename.mp4" on Windows)
    legacy_meeting_id = None
    if meeting.file_path:
        # Handle both forward slashes (Unix) and backslashes (Windows)
        # Normalize path separators to forward slashes first
        normalized_path = meeting.file_path.replace("\\", "/")
        path_parts = normalized_path.split("/")
        if len(path_parts) > 0:
            legacy_meeting_id = path_parts[0]

    return {
        "meeting_id": str(meeting_uuid),
        "insights": insights,
        "file_path": meeting.file_path,
        "legacy_meeting_id": legacy_meeting_id,  # For accessing storage files
        "original_filename": meeting.original_filename,
    }


@router.get("/meetings")
async def list_meetings():
    """List all previous meetings from storage folder."""
    storage_path = Path("storage")
    
    if not storage_path.exists():
        return {"meetings": []}
    
    meetings: List[Dict[str, Any]] = []
    
    for meeting_dir in sorted(storage_path.iterdir(), reverse=True):
        if not meeting_dir.is_dir():
            continue
            
        metadata_file = meeting_dir / "metadata.json"
        if not metadata_file.exists():
            continue
        
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            # Check if insights and transcript exist
            insights_file = meeting_dir / "insights.json"
            transcript_file = meeting_dir / "transcript.json"
            has_insights = insights_file.exists()
            has_transcript = transcript_file.exists()
            
            meetings.append({
                "meeting_id": meeting_dir.name,
                "uuid": metadata.get("uuid"),
                "meeting_name": metadata.get("meeting_name"),
                "upload_timestamp": metadata.get("upload_timestamp"),
                "file_info": metadata.get("file_info", {}),
                "has_insights": has_insights,
                "has_transcript": has_transcript
            })
        except Exception as e:
            print(f"Error reading metadata for {meeting_dir.name}: {e}")
            continue
    
    return {"meetings": meetings}

