from fastapi import APIRouter, HTTPException

from backend.src.api.routes.upload import pipeline_store

router = APIRouter()


@router.get("/status/{meeting_id}")
async def get_status(meeting_id: str):
    status = pipeline_store.get_status(meeting_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"meeting_id": meeting_id, "status": status}

