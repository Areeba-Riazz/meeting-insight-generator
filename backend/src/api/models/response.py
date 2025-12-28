from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class SearchResult(BaseModel):
    """Individual search result."""
    text: str = Field(..., description="The text content that matched")
    meeting_id: str = Field(..., description="ID of the meeting this result belongs to")
    segment_type: str = Field(..., description="Type of segment: transcript, topic, decision, action_item, summary")
    timestamp: Optional[float] = Field(None, description="Timestamp in seconds if available")
    segment_index: Optional[int] = Field(None, description="Index of the segment within its type")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0-1, higher is more similar)")
    distance: float = Field(..., description="L2 distance in embedding space")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata from the segment")


class SearchResponse(BaseModel):
    """Response model for semantic search."""
    query: str = Field(..., description="The search query that was executed")
    results: List[SearchResult] = Field(..., description="List of search results")
    total_results: int = Field(..., description="Total number of results found")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Results per page")
    total_pages: int = Field(..., description="Total number of pages")
    segment_types_filter: Optional[List[str]] = Field(None, description="Segment types that were filtered")
    meeting_ids_filter: Optional[List[str]] = Field(None, description="Meeting IDs that were filtered")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="AI assistant's response")
    sources: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="RAG sources used to generate the response (if RAG was used)"
    )
    used_rag: bool = Field(
        default=False,
        description="Whether RAG was used to generate this response"
    )
