from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from typing import List, Dict, Any

from src.api.routes.upload import pipeline_store

router = APIRouter()


@router.get("/insights/{meeting_id}")
async def get_insights(meeting_id: str):
    # Try to get from in-memory store first
    result = pipeline_store.get_result(meeting_id)
    
    # If not in memory, try to load from storage folder
    if result is None:
        storage_path = Path("storage") / meeting_id / "insights.json"
        if storage_path.exists():
            try:
                with open(storage_path, "r", encoding="utf-8") as f:
                    result = json.load(f)
                print(f"[Insights] Loaded insights from storage for {meeting_id}")
            except Exception as e:
                print(f"[Insights] Error loading insights from storage: {e}")
                raise HTTPException(status_code=404, detail="Meeting not found or not processed yet")
        else:
            raise HTTPException(status_code=404, detail="Meeting not found or not processed yet")
    
    return {"meeting_id": meeting_id, "insights": result}


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

