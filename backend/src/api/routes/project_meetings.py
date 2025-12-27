"""Project meetings routes."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.core.database import get_db
from src.services.database_service import DatabaseService


router = APIRouter()


# Response Models
class ProjectMeetingResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    meeting_name: str
    original_filename: str
    file_size_bytes: int
    content_type: Optional[str]
    status: str
    upload_timestamp: str
    processing_completed_at: Optional[str]
    has_insights: bool
    has_transcript: bool

    class Config:
        from_attributes = True


class ProjectMeetingsResponse(BaseModel):
    meetings: List[ProjectMeetingResponse]
    total: int


@router.get("/projects/{project_id}/meetings", response_model=ProjectMeetingsResponse)
async def list_project_meetings(
    project_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all meetings in a project."""
    # Verify project exists
    db_service = DatabaseService(db)
    project = await db_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get meetings
    meetings = await db_service.get_meetings_by_project(
        project_id=project_id, skip=skip, limit=limit
    )

    # Filter by status if provided
    if status:
        meetings = [m for m in meetings if m.status == status]

    # Get total count
    total = await db_service.count_meetings_by_project(project_id)

    # Build response with additional info
    meeting_responses = []
    for meeting in meetings:
        # Check if insights exist
        transcript = await db_service.get_transcript(meeting.id)
        topics = await db_service.get_topics(meeting.id)
        decisions = await db_service.get_decisions(meeting.id)
        action_items = await db_service.get_action_items(meeting.id)
        summary = await db_service.get_summary(meeting.id)
        
        # Explicitly convert to boolean to avoid None values
        has_insights = bool(
            transcript is not None
            or topics
            or decisions
            or action_items
            or summary
        )

        meeting_responses.append(
            ProjectMeetingResponse(
                id=meeting.id,
                project_id=meeting.project_id,
                meeting_name=meeting.meeting_name,
                original_filename=meeting.original_filename,
                file_size_bytes=meeting.file_size_bytes,
                content_type=meeting.content_type,
                status=meeting.status,
                upload_timestamp=meeting.upload_timestamp.isoformat(),
                processing_completed_at=(
                    meeting.processing_completed_at.isoformat()
                    if meeting.processing_completed_at
                    else None
                ),
                has_insights=has_insights,
                has_transcript=transcript is not None,
            )
        )

    return ProjectMeetingsResponse(meetings=meeting_responses, total=total)


@router.get(
    "/projects/{project_id}/meetings/{meeting_id}", response_model=ProjectMeetingResponse
)
async def get_project_meeting(
    project_id: uuid.UUID,
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get meeting details."""
    # Verify project exists
    db_service = DatabaseService(db)
    project = await db_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get meeting
    meeting = await db_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Verify meeting belongs to project
    if meeting.project_id != project_id:
        raise HTTPException(
            status_code=400, detail="Meeting does not belong to this project"
        )

    # Check if insights exist
    transcript = await db_service.get_transcript(meeting.id)
    topics = await db_service.get_topics(meeting.id)
    decisions = await db_service.get_decisions(meeting.id)
    action_items = await db_service.get_action_items(meeting.id)
    summary = await db_service.get_summary(meeting.id)
    
    # Explicitly convert to boolean to avoid None values
    has_insights = bool(
        transcript is not None
        or topics
        or decisions
        or action_items
        or summary
    )

    return ProjectMeetingResponse(
        id=meeting.id,
        project_id=meeting.project_id,
        meeting_name=meeting.meeting_name,
        original_filename=meeting.original_filename,
        file_size_bytes=meeting.file_size_bytes,
        content_type=meeting.content_type,
        status=meeting.status,
        upload_timestamp=meeting.upload_timestamp.isoformat(),
        processing_completed_at=(
            meeting.processing_completed_at.isoformat()
            if meeting.processing_completed_at
            else None
        ),
        has_insights=has_insights,
        has_transcript=transcript is not None,
    )


@router.delete("/projects/{project_id}/meetings/{meeting_id}", status_code=204)
async def delete_project_meeting(
    project_id: uuid.UUID,
    meeting_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete meeting (cascades to insights)."""
    # Verify project exists
    db_service = DatabaseService(db)
    project = await db_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get meeting
    meeting = await db_service.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Verify meeting belongs to project
    if meeting.project_id != project_id:
        raise HTTPException(
            status_code=400, detail="Meeting does not belong to this project"
        )

    # Delete meeting (cascades to insights)
    success = await db_service.delete_meeting(meeting_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete meeting")

    return None

