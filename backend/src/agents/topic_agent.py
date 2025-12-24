from __future__ import annotations

import re
from typing import Any, Dict, List
from collections import Counter

from .base_agent import BaseAgent


class TopicAgent(BaseAgent):
    """
    Extract key topics from meeting transcript using keyword extraction.
    - Primary: Keyword frequency analysis
    - Fallback: Simple word counting
    """
    name = "topic_agent"

    def __init__(self) -> None:
        pass

    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract keywords using simple frequency-based approach.
        Fallback method without external dependencies.
        """
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
            'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
            'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just'
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        
        # Filter stop words and count
        filtered_words = [w for w in words if w not in stop_words]
        word_freq = Counter(filtered_words)
        
        # Return top N keywords
        return [word for word, _ in word_freq.most_common(top_n)]

    def _extract_topics(self, text: str, segments: List[Dict], top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Extract topics with timestamps using keyword-based approach.
        """
        keywords = self._extract_keywords(text, top_n=top_n * 2)
        
        topics = []
        for keyword in keywords[:top_n]:
            # Find segments containing this keyword
            matching_segments = [
                seg for seg in segments 
                if keyword.lower() in seg.get('text', '').lower()
            ]
            
            if matching_segments:
                first_seg = matching_segments[0]
                last_seg = matching_segments[-1]
                
                # Create topic summary
                context = ' '.join([seg.get('text', '') for seg in matching_segments[:2]])
                
                topics.append({
                    "topic": keyword.capitalize(),
                    "keywords": [keyword],
                    "start": first_seg.get('start', 0),
                    "end": last_seg.get('end', 0),
                    "summary": context[:100] + "..." if len(context) > 100 else context
                })
        
        return topics

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract topics with timestamps.
        
        Returns:
            {
                "topics": [
                    {
                        "topic": "Project Timeline",
                        "keywords": ["deadline", "schedule"],
                        "start": 120.5,
                        "end": 180.2,
                        "summary": "Discussion about deadlines..."
                    }
                ]
            }
        """
        text: str = payload.get("text", "")
        segments: list = payload.get("segments", [])
        
        topics = self._extract_topics(text, segments, top_n=5)
        
        return {"topics": topics}
