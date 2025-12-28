"""Chat endpoint for LLM communication with RAG integration."""

import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.agents.llm_client import LLMClient
from src.agents.config import AgentSettings
from src.api.models.request import ChatRequest
from src.api.models.response import ChatResponse
from src.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize LLM client
_llm_client_instance = None

# Initialize vector store for RAG
_vector_store_path = Path(os.getenv("VECTOR_STORE_PATH", "storage/vectors"))
_embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
_vector_store_instance = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance (singleton pattern)."""
    global _llm_client_instance
    if _llm_client_instance is None:
        logger.info("[Chat] Initializing LLM client")
        settings = AgentSettings()
        _llm_client_instance = LLMClient(settings=settings)
    return _llm_client_instance


def get_vector_store() -> VectorStoreService:
    """Get or create vector store instance (singleton pattern)."""
    global _vector_store_instance
    if _vector_store_instance is None:
        logger.info(f"[Chat] Initializing vector store at: {_vector_store_path.absolute()}")
        _vector_store_instance = VectorStoreService(
            vector_store_path=_vector_store_path,
            embedding_model_name=_embedding_model,
        )
    return _vector_store_instance


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat with the LLM using RAG (Retrieval Augmented Generation).
    
    Accepts a message, optional context, and optional project_id.
    Performs semantic search on meeting content, then generates LLM response with retrieved context.
    """
    try:
        message = request.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        context = request.context
        project_id = request.project_id
        
        # Perform RAG search (always attempt, with or without project_id)
        rag_context = ""
        rag_sources = []  # Store sources for potential frontend display
        try:
            vector_store = get_vector_store()
            # Increase top_k for better analysis - need more context to answer questions
            search_results = vector_store.search(
                query=message,
                top_k=15,  # Get more results for better analysis
                project_id=project_id,  # None for global search, UUID for project-scoped
            )
            
            if search_results:
                # Structure RAG context for better analysis
                rag_context = "\n\n=== RELEVANT MEETING DATA ===\n"
                rag_context += "Use the following meeting content to answer the user's question. Analyze and synthesize this information to provide a direct, helpful answer.\n\n"
                
                # Group results by segment type for better context
                by_type = {}
                for result in search_results[:10]:  # Get more results for better analysis
                    seg_type = result['segment_type']
                    if seg_type not in by_type:
                        by_type[seg_type] = []
                    by_type[seg_type].append(result)
                
                # Present data in a structured way
                for seg_type, results in by_type.items():
                    type_label = seg_type.replace('_', ' ').title()
                    rag_context += f"\n--- {type_label} ---\n"
                    for i, result in enumerate(results, 1):
                        meeting_name = result['meeting_id'].split('_')[0].replace('-', ' ')
                        rag_context += f"[{i}] Meeting: {meeting_name}\n"
                        rag_context += f"Content: {result['text']}\n"
                        if result.get('timestamp'):
                            rag_context += f"Time: {result['timestamp']:.1f}s\n"
                        rag_context += "\n"
                
                # Store sources for frontend
                for result in search_results[:5]:
                    rag_sources.append({
                        'meeting_id': result['meeting_id'],
                        'segment_type': result['segment_type'],
                        'text': result['text'][:200],
                        'similarity': result.get('similarity_score', 0)
                    })
                logger.info(f"[Chat] Retrieved {len(search_results)} relevant results from RAG search (project_id: {project_id})")
            else:
                logger.info(f"[Chat] No relevant results found in RAG search (project_id: {project_id})")
        except Exception as e:
            logger.warning(f"[Chat] RAG search failed: {e}. Continuing without RAG context.", exc_info=True)
        
        # Build system prompt with context and RAG results
        system_prompt_parts = [
            "You are an intelligent AI assistant for a meeting insights application.",
            "Your role is to ANALYZE meeting data and provide direct, helpful answers to user questions.",
            "",
            "IMPORTANT INSTRUCTIONS:",
            "1. When provided with meeting data, ANALYZE it to answer the user's question directly.",
            "2. Do NOT just summarize or repeat the retrieved text. Instead, reason about the data and provide insights.",
            "3. For questions like 'who is the most absent student' or 'what are the main decisions', analyze ALL the provided data and give a synthesized answer.",
            "4. If the question requires comparing or ranking items (e.g., 'most absent', 'most discussed'), analyze the data and provide the answer.",
            "5. Cite specific meetings or segments when relevant, but focus on answering the question directly.",
            "6. If the data doesn't contain enough information to answer, say so clearly.",
        ]
        
        if context:
            system_prompt_parts.append(f"\nCurrent context: {context}")
        
        if project_id:
            system_prompt_parts.append(f"\nNote: The user is viewing project ID: {project_id}. All meeting data below is from this project.")
        
        if rag_context:
            system_prompt_parts.append(f"\n{rag_context}")
            system_prompt_parts.append("\n=== END OF MEETING DATA ===")
            system_prompt_parts.append("\nNow analyze the above meeting data and answer the user's question directly. Provide a clear, concise answer based on your analysis of the data.")
        else:
            if project_id:
                system_prompt_parts.append(f"\nNo relevant meeting content found in project {project_id}.")
            system_prompt_parts.append("\nPlease provide helpful, concise responses based on your general knowledge about meetings, transcripts, insights, and related topics.")
        
        system_prompt = "\n".join(system_prompt_parts)
        
        # Get LLM client and generate response
        llm_client = get_llm_client()
        logger.info(f"[Chat] Processing message: '{message[:50]}...' (project_id: {project_id}, RAG: {bool(rag_context)})")
        
        # Use a more conversational prompt that encourages analysis
        user_prompt = message
        if rag_context:
            # When we have RAG context, frame it as an analysis task
            user_prompt = f"""Based on the meeting data provided below, please answer this question: {message}

Analyze the data, identify patterns, compare information, and provide a direct answer. Do not just summarize the chunks - actually reason about the data to answer the question."""
        
        response = await llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt
        )
        
        logger.info(f"[Chat] Generated response: '{response[:50]}...'")
        
        return ChatResponse(
            response=response,
            sources=rag_sources if rag_sources else None,
            used_rag=bool(rag_sources)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Chat] Error processing chat message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)[:200]}"
        )

