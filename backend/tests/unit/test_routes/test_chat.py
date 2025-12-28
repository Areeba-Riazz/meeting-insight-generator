"""Unit tests for chat route."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException

from src.api.routes.chat import chat
from src.api.models.request import ChatRequest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_success():
    """Test successful chat with RAG context."""
    message = "What was discussed?"
    mock_search_results = [
        {
            "meeting_id": "meeting1",
            "text": "Meeting discussed topics A, B, and C.",
            "segment_type": "transcript",
            "similarity_score": 0.9
        }
    ]
    mock_response = "Based on the meeting, topics A, B, and C were discussed."
    
    mock_vector_store = MagicMock()
    # search is not async, it's a regular method
    mock_vector_store.search = MagicMock(return_value=mock_search_results)
    
    mock_llm_client = MagicMock()
    mock_llm_client.generate = AsyncMock(return_value=mock_response)
    
    request = ChatRequest(message=message)
    
    with patch('src.api.routes.chat.get_vector_store', return_value=mock_vector_store):
        with patch('src.api.routes.chat.get_llm_client', return_value=mock_llm_client):
            result = await chat(request)
            
            assert result.response == mock_response
            # used_rag is True when rag_sources is not empty (rag_sources populated from search_results[:5])
            assert result.used_rag is True
            assert result.sources is not None
            assert len(result.sources) > 0
            mock_vector_store.search.assert_called_once()
            mock_llm_client.generate.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_no_rag_context():
    """Test chat when no RAG context is found."""
    message = "What was discussed?"
    mock_response = "I don't have specific meeting context to answer this."
    
    mock_vector_store = MagicMock()
    mock_vector_store.search = MagicMock(return_value=[])  # No results - search is not async
    
    mock_llm_client = MagicMock()
    mock_llm_client.generate = AsyncMock(return_value=mock_response)
    
    request = ChatRequest(message=message)
    
    with patch('src.api.routes.chat.get_vector_store', return_value=mock_vector_store):
        with patch('src.api.routes.chat.get_llm_client', return_value=mock_llm_client):
            result = await chat(request)
            
            assert result.response == mock_response
            assert result.used_rag is False  # No RAG sources when no results


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_empty_message():
    """Test chat with empty message."""
    request = ChatRequest(message="   ")
    
    with pytest.raises(HTTPException) as exc_info:
        await chat(request)
    
    assert exc_info.value.status_code == 400
    assert "empty" in str(exc_info.value.detail).lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_llm_error():
    """Test chat when LLM call fails."""
    message = "What was discussed?"
    
    mock_vector_store = MagicMock()
    mock_vector_store.search = MagicMock(return_value=[])  # search is not async
    
    mock_llm_client = MagicMock()
    mock_llm_client.generate = AsyncMock(side_effect=Exception("LLM error"))
    
    request = ChatRequest(message=message)
    
    with patch('src.api.routes.chat.get_vector_store', return_value=mock_vector_store):
        with patch('src.api.routes.chat.get_llm_client', return_value=mock_llm_client):
            with pytest.raises(HTTPException) as exc_info:
                await chat(request)
            
            assert exc_info.value.status_code == 500

