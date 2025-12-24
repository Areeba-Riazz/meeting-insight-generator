from __future__ import annotations

import re
from typing import Any, Dict, Optional
from collections import Counter

from .base_agent import BaseAgent


class HuggingFaceClient:
    """Client for HuggingFace Inference API with error handling."""
    
    def __init__(self, token: Optional[str] = None):
        import os
        self.token = token or os.getenv("HUGGINGFACE_TOKEN")
        self.base_url = "https://api-inference.huggingface.co/models"
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def query(self, model: str, inputs: Dict[str, Any], timeout: int = 30) -> Optional[Dict]:
        """Query HuggingFace model with error handling."""
        if not self.token:
            return None
        
        try:
            import requests
            response = requests.post(
                f"{self.base_url}/{model}",
                headers=self.headers,
                json=inputs,
                timeout=timeout
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"[HuggingFace API Error] {e}")
            return None


class SummaryAgent(BaseAgent):
    """
    Generate meeting summary using extractive and abstractive techniques.
    - Primary: HuggingFace BART model for abstractive summary
    - Fallback: TextRank algorithm for extractive summary
    """
    name = "summary_agent"

    def __init__(self) -> None:
        self.hf_client = HuggingFaceClient()

    def _extractive_summary(self, text: str, num_sentences: int = 3) -> str:
        """
        Extractive summarization using TextRank-like algorithm.
        Fallback method that doesn't require external models.
        """
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if len(sentences) <= num_sentences:
            return text
        
        # Simple scoring: sentence length and position
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            words = sentence.split()
            # Score based on length (prefer medium-length) and position (prefer early)
            length_score = min(len(words) / 20.0, 1.0)
            position_score = 1.0 - (i / len(sentences))
            score = (length_score * 0.7) + (position_score * 0.3)
            scored_sentences.append((score, sentence))
        
        # Sort by score and take top N
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        top_sentences = [s[1] for s in scored_sentences[:num_sentences]]
        
        # Return in original order
        result = []
        for sentence in sentences:
            if sentence in top_sentences:
                result.append(sentence)
        
        return '. '.join(result) + '.'

    def _abstractive_summary(self, text: str, max_length: int = 150) -> Optional[str]:
        """
        Abstractive summarization using HuggingFace BART model.
        Returns None if API fails.
        """
        # Truncate text if too long (BART has 1024 token limit)
        max_input_length = 1024
        words = text.split()
        if len(words) > max_input_length:
            text = ' '.join(words[:max_input_length])
        
        result = self.hf_client.query(
            "facebook/bart-large-cnn",
            {"inputs": text, "parameters": {"max_length": max_length, "min_length": 30}}
        )
        
        if result and isinstance(result, list) and len(result) > 0:
            return result[0].get("summary_text", "")
        return None

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate both extractive and abstractive summaries.
        
        Returns:
            {
                "summary": {
                    "extractive": "Key sentences...",
                    "abstractive": "AI-generated summary...",
                    "combined": "Best summary..."
                }
            }
        """
        text: str = payload.get("text", "")
        
        # Try abstractive first (HuggingFace API)
        abstractive = self._abstractive_summary(text)
        
        # Always generate extractive as fallback
        extractive = self._extractive_summary(text, num_sentences=3)
        
        summary_result = {
            "extractive": extractive,
            "abstractive": abstractive or extractive,
            "combined": abstractive if abstractive else extractive
        }
        
        return {"summary": summary_result}
