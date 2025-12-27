"""Chat endpoint for LLM communication."""

import logging

from fastapi import APIRouter, HTTPException

from src.agents.llm_client import LLMClient
from src.agents.config import AgentSettings
from src.api.models.request import ChatRequest
from src.api.models.response import ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize LLM client
_llm_client_instance = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance (singleton pattern)."""
    global _llm_client_instance
    if _llm_client_instance is None:
        logger.info("[Chat] Initializing LLM client")
        settings = AgentSettings()
        _llm_client_instance = LLMClient(settings=settings)
    return _llm_client_instance


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat with the LLM.
    
    Accepts a message and optional context, returns LLM response.
    """
    try:
        message = request.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        context = request.context
        
        # Build system prompt with context if provided
        system_prompt = None
        if context:
            system_prompt = f"""You are a helpful AI assistant for a meeting insights application. 
The user is working with meeting data. Here's some context about what they're viewing:
{context}

Please provide helpful, concise responses about their meetings and data."""
        else:
            system_prompt = """You are a helpful AI assistant for a meeting insights application. 
Please provide helpful, concise responses about meetings, transcripts, insights, and related topics."""
        
        # Get LLM client and generate response
        llm_client = get_llm_client()
        logger.info(f"[Chat] Processing message: '{message[:50]}...'")
        
        response = await llm_client.generate(
            prompt=message,
            system_prompt=system_prompt
        )
        
        logger.info(f"[Chat] Generated response: '{response[:50]}...'")
        
        return ChatResponse(response=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Chat] Error processing chat message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)[:200]}"
        )

