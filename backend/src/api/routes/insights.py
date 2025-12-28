import json
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.db_models import Meeting
from src.services.database_service import DatabaseService
from src.api.routes.upload import pipeline_store

router = APIRouter()


@router.get("/insights/{meeting_id}")
async def get_insights(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
):
    # Try to parse as UUID first
    try:
        meeting_uuid = uuid.UUID(meeting_id)
    except ValueError:
        # Legacy meeting_id format (folder name) - try database first by file_path
        db_service = DatabaseService(db)
        
        # Try to find meeting in database by file_path (contains the legacy meeting_id)
        # file_path format is: "meeting_id/audio/filename.mp4" or "meeting_id\audio\filename.mp4"
        # Use SQL LIKE to match either forward or backward slashes
        result = await db.execute(
            select(Meeting).where(
                or_(
                    Meeting.file_path.like(f"{meeting_id}/%"),
                    Meeting.file_path.like(f"{meeting_id}\\%")
                )
            )
        )
        db_meeting = result.scalar_one_or_none()
        
        if db_meeting:
            # Found in database, load insights from database
            insights = await db_service.get_all_insights(db_meeting.id)
            if insights:
                return {
                    "meeting_id": str(db_meeting.id),
                    "insights": insights,
                    "legacy_meeting_id": meeting_id,
                    "file_path": db_meeting.file_path,
                    "original_filename": db_meeting.original_filename,
                }
        
        # Try in-memory store
        result = pipeline_store.get_result(meeting_id)
        if result:
            return {
                "meeting_id": meeting_id,
                "insights": result,
                "legacy_meeting_id": meeting_id,
            }
        
        # Fallback to storage folder
        storage_path = Path("storage") / meeting_id
        insights_file = storage_path / "insights.json"
        if insights_file.exists():
            try:
                with open(insights_file, "r", encoding="utf-8") as f:
                    insights = json.load(f)
                
                # Get metadata for original_filename
                metadata_file = storage_path / "metadata.json"
                original_filename = None
                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as mf:
                            metadata = json.load(mf)
                            original_filename = metadata.get("file_info", {}).get("original_filename")
                    except Exception:
                        pass
                
                return {
                    "meeting_id": meeting_id,
                    "insights": insights,
                    "legacy_meeting_id": meeting_id,
                    "original_filename": original_filename,
                }
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error reading insights file: {str(e)}"
                )
        
        raise HTTPException(
            status_code=404,
            detail=f"Meeting not found: {meeting_id}. Checked database, in-memory store, and storage folder.",
        )

    # Load from database
    db_service = DatabaseService(db)
    meeting = await db_service.get_meeting(meeting_uuid)
    
    if not meeting:
        # Fallback to in-memory store
        result = pipeline_store.get_result(meeting_id)
        if result:
            return {"meeting_id": meeting_id, "insights": result}
        
        # Also try to find by UUID in storage metadata files
        storage_path = Path("storage")
        if storage_path.exists():
            for meeting_dir in storage_path.iterdir():
                if not meeting_dir.is_dir():
                    continue
                metadata_file = meeting_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as mf:
                            metadata = json.load(mf)
                            if metadata.get("uuid") == str(meeting_uuid):
                                # Found matching UUID, load insights
                                insights_file = meeting_dir / "insights.json"
                                if insights_file.exists():
                                    with open(insights_file, "r", encoding="utf-8") as f:
                                        insights = json.load(f)
                                    return {
                                        "meeting_id": str(meeting_uuid),
                                        "insights": insights,
                                        "legacy_meeting_id": meeting_dir.name,
                                        "original_filename": metadata.get("file_info", {}).get("original_filename"),
                                    }
                    except Exception:
                        continue
        
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

