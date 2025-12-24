from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional

from .base_agent import BaseAgent
from .llm_client import get_mistral_completion


class SummaryAgent(BaseAgent):
    """
    Generate comprehensive meeting summary using Mistral AI.
    Creates extractive (key quotes) and abstractive (AI-generated) summaries.
    """
    name = "summary_agent"

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.getenv("MISTRAL_API_KEY")

    def _create_extractive_summary(self, text: str, segments: list = None, num_sentences: int = 5):
        """Extract most important sentences for key excerpts with timestamps."""
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip() and len(s.strip()) > 20]
        
        # Score sentences by length, position, and key indicators
        scored_sentences = []
        key_indicators = ['important', 'key', 'main', 'critical', 'essential', 'decided', 'agreed', 'action']
        
        for i, sentence in enumerate(sentences):
            words = sentence.lower().split()
            
            # Length score (prefer medium-length sentences)
            length_score = min(len(words) / 25.0, 1.0)
            
            # Position score (prefer early and late sentences)
            position = i / len(sentences)
            position_score = 1.0 - abs(0.5 - position)
            
            # Keyword score
            keyword_score = sum(1 for indicator in key_indicators if indicator in sentence.lower()) / len(key_indicators)
            
            # Combined score
            score = (length_score * 0.4) + (position_score * 0.3) + (keyword_score * 0.3)
            scored_sentences.append((score, sentence))
        
        # Sort and select top sentences
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        top_sentences = [s[1] for s in scored_sentences[:min(num_sentences, len(scored_sentences))]]
        
        # Find timestamps for each sentence by matching to segments
        excerpts = []
        if segments:
            for sentence in top_sentences:
                # Find the segment that contains this sentence (or part of it)
                timestamp = None
                for seg in segments:
                    seg_text = seg.get('text', '').strip()
                    # Check if sentence is in segment or vice versa (fuzzy match)
                    if sentence[:30].lower() in seg_text.lower() or seg_text[:30].lower() in sentence.lower():
                        timestamp = seg.get('start', 0)
                        break
                
                excerpts.append({
                    "text": sentence,
                    "timestamp": timestamp if timestamp is not None else 0
                })
        else:
            # If no segments, return sentences without timestamps
            excerpts = [{"text": s, "timestamp": None} for s in top_sentences]
        
        # Also return as string for backward compatibility
        excerpt_string = '. '.join(top_sentences) + '.' if top_sentences else ""
        
        return {"excerpts": excerpts, "text": excerpt_string}

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive meeting summary.
        
        Returns:
            {
                "summary": {
                    "extractive": {"excerpts": [...], "text": "..."},
                    "abstractive": "AI-generated summary...",
                    "combined": "Main summary..."
                }
            }
        """
        text: str = payload.get("text", "")
        segments: list = payload.get("segments", [])
        
        if not text or len(text) < 50:
            return {"summary": "Transcript too short to summarize."}
        
        # Truncate if too long
        max_words = 3000
        words = text.split()
        if len(words) > max_words:
            text = ' '.join(words[:max_words]) + "..."
        
        # Generate extractive summary (key excerpts) with timestamps
        extractive = self._create_extractive_summary(text, segments=segments, num_sentences=5)
        
        # Generate abstractive summary using Mistral AI
        prompt = f"""You are an expert at summarizing meetings. Generate a comprehensive, well-structured summary of this meeting transcript.

Transcript:
{text}

Create a clear, professional summary that:
1. Captures the main purpose and outcomes of the meeting
2. Highlights key discussion points and topics
3. Notes any decisions made or action items mentioned
4. Is concise but informative (3-5 paragraphs)
5. Uses professional business language

Summary:"""

        try:
            abstractive = await get_mistral_completion(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3,
                api_key=self.token
            )
            abstractive = abstractive.strip() if abstractive else None
        except Exception as e:
            print(f"[SummaryAgent] Mistral API error: {e}")
            abstractive = None
        
        # Fallback to extractive if AI fails
        if not abstractive or len(abstractive) < 50:
            abstractive = extractive.get("text", "")
        
        summary_result = {
            "extractive": extractive,
            "abstractive": abstractive,
            "combined": abstractive
        }
        
        return {"summary": summary_result}
