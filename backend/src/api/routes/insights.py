from fastapi import APIRouter, HTTPException

from src.api.routes.upload import pipeline_store

router = APIRouter()


@router.get("/insights/{meeting_id}")
async def get_insights(meeting_id: str):
    result = pipeline_store.get_result(meeting_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Meeting not found or not processed yet")
    return {"meeting_id": meeting_id, "insights": result}

