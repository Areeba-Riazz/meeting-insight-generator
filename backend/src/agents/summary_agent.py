from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional

from .base_agent import BaseAgent
from .llm_client import get_mistral_completion


class SummaryAgent(BaseAgent):
    """
    Generate comprehensive meeting summary using Mistral AI and extractive methods.
    
    - **Paragraph Summary**: Mistral AI-generated comprehensive overview
    - **Bullet Points**: Mistral AI-generated key takeaways (5-8 points, no timestamps)
    - **Key Excerpts**: Verbatim quotes from transcript with timestamps
    
    Bullet points are AI-generated insights.
    Key excerpts are actual quotes from what was said in the meeting.
    """
    name = "summary_agent"

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.getenv("MISTRAL_API_KEY")

    def _extract_key_quotes(self, text: str, segments: list = None, num_quotes: int = 5) -> dict:
        """
        Extract actual verbatim quotes from the transcript with timestamps.
        These are real excerpts from what was said, not AI-generated summaries.
        
        Args:
            text: Full transcript text
            segments: List of transcript segments with timestamps
            num_quotes: Number of key quotes to extract
            
        Returns:
            Dictionary with excerpts list (quotes with timestamps) and text string
        """
        if not segments:
            # If no segments, extract sentences from text without timestamps
            sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip() and len(s.strip()) > 30]
            top_quotes = sentences[:num_quotes]
            excerpts = [{"text": quote, "timestamp": None} for quote in top_quotes]
            return {"excerpts": excerpts, "text": '. '.join(top_quotes) + '.'}
        
        # Score segments by importance indicators
        scored_segments = []
        key_indicators = ['important', 'key', 'decided', 'agreed', 'action', 'need to', 'should', 
                         'will', 'must', 'critical', 'essential', 'main point', 'conclusion']
        
        for seg in segments:
            seg_text = seg.get('text', '').strip()
            if len(seg_text) < 30:  # Skip very short segments
                continue
            
            words = seg_text.lower().split()
            
            # Length score (prefer medium-length quotes)
            length_score = min(len(words) / 20.0, 1.0)
            
            # Keyword score (look for important phrases)
            keyword_score = sum(1 for indicator in key_indicators if indicator in seg_text.lower())
            keyword_score = min(keyword_score / 3.0, 1.0)  # Normalize
            
            # Combined score
            score = (length_score * 0.5) + (keyword_score * 0.5)
            
            scored_segments.append({
                'score': score,
                'text': seg_text,
                'start': seg.get('start', 0),
                'end': seg.get('end', 0)
            })
        
        # Sort by score and take top quotes
        scored_segments.sort(key=lambda x: x['score'], reverse=True)
        top_segments = scored_segments[:num_quotes]
        
        # Sort by timestamp for chronological order
        top_segments.sort(key=lambda x: x['start'])
        
        # Create excerpts with timestamps
        excerpts = []
        for seg in top_segments:
            excerpts.append({
                "text": seg['text'],
                "timestamp": seg['start']
            })
        
        # Create text string
        excerpt_string = '. '.join([e['text'] for e in excerpts]) + '.' if excerpts else ""
        
        return {"excerpts": excerpts, "text": excerpt_string}

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive meeting summary using Mistral AI and extractive methods.
        
        Returns:
            {
                "summary": {
                    "extractive": {
                        "excerpts": [
                            {"text": "Actual quote from transcript", "timestamp": 45.2},
                            ...
                        ],
                        "text": "Combined quotes as text"
                    },
                    "abstractive": {
                        "paragraph": "Mistral AI-generated paragraph summary",
                        "bullets": ["AI-generated bullet 1", "AI-generated bullet 2", ...]
                    },
                    "combined": "Paragraph summary (for backward compatibility)"
                }
            }
            
        Note: 
        - extractive.excerpts = Verbatim quotes from transcript WITH timestamps
        - abstractive.bullets = AI-generated key points WITHOUT timestamps
        - abstractive.paragraph = AI-generated comprehensive summary
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
        
        # Generate paragraph summary using Mistral AI
        paragraph_prompt = f"""You are an expert at summarizing meetings. Generate a comprehensive, well-structured summary of this meeting transcript.

Transcript:
{text}

Create a clear, professional summary that:
1. Captures the main purpose and outcomes of the meeting
2. Highlights key discussion points and topics
3. Notes any decisions made or action items mentioned
4. Is concise but informative (3-5 paragraphs)
5. Uses professional business language

Summary:"""

        # Generate bullet point summary using Mistral AI
        bullet_prompt = f"""You are an expert at summarizing meetings. Generate a concise bullet-point summary of this meeting transcript.

Transcript:
{text}

Create 5-8 key bullet points that capture:
- Main topics discussed
- Key decisions made
- Important action items
- Critical outcomes or conclusions

Format as a simple list with each point on a new line, starting with a dash (-). Be concise and specific.

Bullet Points:"""

        try:
            # Get paragraph summary
            paragraph_summary = await get_mistral_completion(
                prompt=paragraph_prompt,
                max_tokens=500,
                temperature=0.3,
                api_key=self.token
            )
            paragraph_summary = paragraph_summary.strip() if paragraph_summary else None
            
            # Get bullet point summary
            bullet_summary = await get_mistral_completion(
                prompt=bullet_prompt,
                max_tokens=400,
                temperature=0.3,
                api_key=self.token
            )
            
            # Parse bullet points into list
            bullet_points = []
            if bullet_summary:
                bullet_summary = bullet_summary.strip()
                # Split by newlines and clean up
                lines = [line.strip() for line in bullet_summary.split('\n') if line.strip()]
                for line in lines:
                    # Remove leading dashes, asterisks, or numbers
                    cleaned = re.sub(r'^[-*•]\s*', '', line)
                    cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
                    if cleaned:
                        bullet_points.append(cleaned)
            
        except Exception as e:
            print(f"[SummaryAgent] Mistral API error: {e}")
            paragraph_summary = None
            bullet_points = []
        
        # Extract actual verbatim quotes from the transcript with timestamps
        # These are real quotes from what was said, not AI-generated
        extractive = self._extract_key_quotes(text, segments=segments, num_quotes=5)
        
        # Fallback for paragraph if AI failed
        if not paragraph_summary or len(paragraph_summary) < 50:
            paragraph_summary = extractive.get("text", "No summary available")
        
        # Fallback for bullets if AI failed
        if not bullet_points:
            bullet_points = [excerpt["text"] for excerpt in extractive.get("excerpts", [])[:5]]
        
        # Abstractive contains AI-generated content (no timestamps on bullets)
        abstractive_result = {
            "paragraph": paragraph_summary,
            "bullets": bullet_points  # AI-generated key points (no timestamps)
        }
        
        summary_result = {
            "extractive": extractive,  # Verbatim quotes with timestamps
            "abstractive": abstractive_result,  # AI-generated summaries
            "combined": paragraph_summary  # Keep paragraph as default combined view
        }
        
        return {"summary": summary_result}