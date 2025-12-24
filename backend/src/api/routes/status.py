from fastapi import APIRouter, HTTPException

from src.api.routes.upload import pipeline_store

router = APIRouter()


@router.get("/status/{meeting_id}")
async def get_status(meeting_id: str):
    status = pipeline_store.get_status(meeting_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Get progress and stage information
    progress = pipeline_store.get_progress(meeting_id)
    stage = pipeline_store.get_stage(meeting_id)
    
    return {
        "meeting_id": meeting_id,
        "status": status,
        "progress": progress,
        "stage": stage,
        "estimated_time_remaining": None  # Optional: can be calculated based on historical data
    }

