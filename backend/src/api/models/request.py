from typing import List, Optional

from pydantic import BaseModel, Field


class UploadRequest(BaseModel):
    filename: str
    content_type: str | None = None


class SearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str = Field(..., description="Search query text", min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    segment_types: Optional[List[str]] = Field(
        default=None,
        description="Filter by segment types: transcript, topic, decision, action_item, summary"
    )
    meeting_ids: Optional[List[str]] = Field(
        default=None,
        description="Filter by specific meeting IDs"
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Filter by project ID (UUID) - searches only meetings in this project"
    )
    min_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score (0-1, higher is more similar)"
    )
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    page_size: int = Field(default=10, ge=1, le=100, description="Results per page")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message", min_length=1, max_length=2000)
    context: Optional[str] = Field(
        default=None,
        description="Optional context about the current page/view",
        max_length=1000
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID (UUID) for project-scoped RAG search"
    )
