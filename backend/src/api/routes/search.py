"""Search endpoint for semantic search across meetings."""

import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.api.models.request import SearchRequest
from src.api.models.response import SearchResponse, SearchResult
from src.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize vector store (shared with upload route)
# Use same path resolution as upload route
_vector_store_path = Path(os.getenv("VECTOR_STORE_PATH", "storage/vectors"))
_embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Create singleton instance
_vector_store_instance = None

def get_vector_store() -> VectorStoreService:
    """Get or create vector store instance (singleton pattern)."""
    global _vector_store_instance
    if _vector_store_instance is None:
        logger.info(f"[Search] Initializing vector store at: {_vector_store_path.absolute()}")
        _vector_store_instance = VectorStoreService(
            vector_store_path=_vector_store_path,
            embedding_model_name=_embedding_model,
        )
        stats = _vector_store_instance.get_stats()
        logger.info(f"[Search] Vector store initialized. Total vectors: {stats['total_vectors']}")
        if stats['total_vectors'] == 0:
            logger.warning("[Search] No vectors found in index. Upload a meeting first to create embeddings.")
    return _vector_store_instance

# Initialize on module load
vector_store = get_vector_store()


@router.post("/search", response_model=SearchResponse)
async def search_meetings(request: SearchRequest) -> SearchResponse:
    """
    Perform semantic search across all meeting content.
    
    Searches through:
    - Meeting transcripts (chunked)
    - Topics
    - Decisions
    - Action items
    - Summaries
    
    Returns results ranked by semantic similarity.
    """
    try:
        # Preprocess query (basic cleaning)
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if len(query) > 500:
            query = query[:500]
            logger.warning(f"[Search] Query truncated to 500 characters")
        
        # Perform search
        logger.info(f"[Search] Searching for: '{query[:50]}...' (top_k={request.top_k})")
        
        # Get vector store instance (reload to ensure latest data)
        vs = get_vector_store()
        
        # Get more results than needed for pagination
        search_top_k = request.top_k * request.page_size if request.page_size else request.top_k * 10
        
        raw_results = vs.search(
            query=query,
            top_k=search_top_k,
            segment_types=request.segment_types,
            meeting_ids=request.meeting_ids,
            min_score=request.min_score,
        )
        
        # Apply pagination
        total_results = len(raw_results)
        start_idx = (request.page - 1) * request.page_size
        end_idx = start_idx + request.page_size
        paginated_results = raw_results[start_idx:end_idx]
        
        # Convert to response models
        results = [
            SearchResult(
                text=r["text"],
                meeting_id=r["meeting_id"],
                segment_type=r["segment_type"],
                timestamp=r.get("timestamp"),
                segment_index=r.get("segment_index"),
                similarity_score=r["similarity_score"],
                distance=r["distance"],
                additional_data=r.get("additional_data"),
            )
            for r in paginated_results
        ]
        
        # Calculate total pages
        total_pages = (total_results + request.page_size - 1) // request.page_size if request.page_size > 0 else 1
        
        logger.info(
            f"[Search] Found {total_results} results, returning page {request.page}/{total_pages} "
            f"({len(results)} results)"
        )
        
        return SearchResponse(
            query=query,
            results=results,
            total_results=total_results,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
            segment_types_filter=request.segment_types,
            meeting_ids_filter=request.meeting_ids,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Search] Error performing search: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)[:200]}"
        )


@router.get("/search/stats")
async def get_search_stats() -> dict:
    """Get statistics about the vector store."""
    try:
        vs = get_vector_store()
        stats = vs.get_stats()
        return stats
    except Exception as e:
        logger.error(f"[Search] Error getting stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)[:200]}"
        )

