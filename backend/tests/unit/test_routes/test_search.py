"""Unit tests for search route."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException

from src.api.routes.search import search_meetings
from src.api.models.request import SearchRequest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_meetings_success():
    """Test successful meeting search."""
    mock_results = [
        {
            "meeting_id": "meeting1",
            "text": "Test meeting content",
            "similarity_score": 0.95,
            "distance": 0.05,
            "segment_type": "transcript",
            "timestamp": None,
            "segment_index": None,
        },
        {
            "meeting_id": "meeting2",
            "text": "Another test",
            "similarity_score": 0.85,
            "distance": 0.15,
            "segment_type": "topic",
            "timestamp": None,
            "segment_index": None,
        }
    ]
    
    request = SearchRequest(query="test query", top_k=10, page_size=10, page=1)
    
    mock_vector_store = MagicMock()
    # search is a regular method, not async
    mock_vector_store.search = MagicMock(return_value=mock_results)
    mock_vector_store.get_stats = MagicMock(return_value={"total_vectors": 100})
    mock_vector_store.count_vectors_by_project = MagicMock(return_value=50)
    
    with patch('src.api.routes.search.get_vector_store', return_value=mock_vector_store):
        result = await search_meetings(request)
        
        assert result.query == "test query"
        assert len(result.results) == 2
        assert result.total_results == 2
        mock_vector_store.search.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_meetings_empty_query():
    """Test search with empty query."""
    request = SearchRequest(query="   ", top_k=10, page_size=10, page=1)
    
    with pytest.raises(HTTPException) as exc_info:
        await search_meetings(request)
    
    assert exc_info.value.status_code == 400
    assert "empty" in str(exc_info.value.detail).lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_meetings_no_results():
    """Test search with no results."""
    request = SearchRequest(query="nonexistent content", top_k=10, page_size=10, page=1)
    
    mock_vector_store = MagicMock()
    # search is not async - it's a regular method
    mock_vector_store.search = MagicMock(return_value=[])
    mock_vector_store.get_stats = MagicMock(return_value={"total_vectors": 0})
    mock_vector_store.count_vectors_by_project = MagicMock(return_value=0)
    
    with patch('src.api.routes.search.get_vector_store', return_value=mock_vector_store):
        result = await search_meetings(request)
        
        assert len(result.results) == 0
        assert result.query == "nonexistent content"
        assert result.total_results == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_meetings_with_pagination():
    """Test search with pagination."""
    mock_results = [
        {
            "meeting_id": f"meeting{i}",
            "text": "content",
            "similarity_score": 0.9,
            "distance": 0.1,
            "segment_type": "transcript"
        }
        for i in range(20)
    ]
    
    request = SearchRequest(query="test query", top_k=10, page_size=5, page=1)
    
    mock_vector_store = MagicMock()
    # search is a regular method, not async
    mock_vector_store.search = MagicMock(return_value=mock_results)
    mock_vector_store.get_stats = MagicMock(return_value={"total_vectors": 100})
    mock_vector_store.count_vectors_by_project = MagicMock(return_value=50)
    
    with patch('src.api.routes.search.get_vector_store', return_value=mock_vector_store):
        result = await search_meetings(request)
        
        assert len(result.results) == 5  # page_size
        assert result.total_results == 20


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_meetings_vector_store_error():
    """Test search when vector store raises an error."""
    request = SearchRequest(query="test query", top_k=10, page_size=10, page=1)
    
    mock_vector_store = MagicMock()
    # search is not async - it's a regular method
    mock_vector_store.search = MagicMock(side_effect=Exception("Vector store error"))
    mock_vector_store.get_stats = MagicMock(return_value={"total_vectors": 0})
    mock_vector_store.count_vectors_by_project = MagicMock(return_value=0)
    
    with patch('src.api.routes.search.get_vector_store', return_value=mock_vector_store):
        with pytest.raises(HTTPException) as exc_info:
            await search_meetings(request)
        
        assert exc_info.value.status_code == 500

