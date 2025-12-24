from __future__ import annotations

import os
import json
import re
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent
from .llm_client import get_mistral_completion


class TopicAgent(BaseAgent):
    """
    Extract meaningful topics from meeting transcript using Mistral AI.
    Identifies discussion themes with timestamps and summaries.
    """
    name = "topic_agent"

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.getenv("MISTRAL_API_KEY")

    def _find_topic_timestamps(self, topic_keywords: List[str], segments: List[Dict]) -> tuple:
        """Find start and end timestamps for a topic based on keywords."""
        matching_segments = []
        
        for seg in segments:
            text = seg.get('text', '').lower()
            if any(keyword.lower() in text for keyword in topic_keywords):
                matching_segments.append(seg)
        
        if matching_segments:
            return (
                matching_segments[0].get('start', 0),
                matching_segments[-1].get('end', 0)
            )
        return (0, 0)

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key topics with timestamps and summaries.
        
        Returns:
            {
                "topics": [
                    {
                        "topic": "PowerPoint Tips for Teachers",
                        "start": 0,
                        "end": 120,
                        "summary": "Introduction to PowerPoint features..."
                    }
                ]
            }
        """
        text: str = payload.get("text", "")
        segments: list = payload.get("segments", [])
        
        if not text or len(text) < 50:
            return {"topics": []}
        
        # Truncate if too long
        max_words = 2000
        words = text.split()
        if len(words) > max_words:
            text = ' '.join(words[:max_words]) + "..."
        
        # Use Mistral AI to identify topics
        prompt = f"""You are an expert at analyzing meeting transcripts. Identify the main topics/themes discussed in this transcript.

Transcript:
{text}

Identify 3-7 distinct topics that were discussed. For each topic, provide:
1. A clear, descriptive topic name (3-8 words)
2. Key keywords mentioned (2-4 words)
3. A brief summary of what was discussed (1-2 sentences)

Return ONLY a valid JSON array with this exact format:
[
  {{
    "topic": "Topic Name",
    "keywords": ["keyword1", "keyword2"],
    "summary": "Brief summary of the discussion."
  }}
]

Topics:"""

        try:
            response = await get_mistral_completion(
                prompt=prompt,
                max_tokens=800,
                temperature=0.3,
                api_key=self.token
            )
            
            # Parse JSON response
            response = response.strip()
            # Extract JSON array if wrapped in text
            json_match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)
            
            topics_data = json.loads(response)
            
            # Add timestamps to each topic
            topics = []
            for topic in topics_data:
                keywords = topic.get('keywords', [topic.get('topic', '').split()[0]])
                start, end = self._find_topic_timestamps(keywords, segments)
                
                topics.append({
                    "topic": topic.get('topic', 'Unknown Topic'),
                    "start": start,
                    "end": end,
                    "summary": topic.get('summary', '')
                })
            
            return {"topics": topics if topics else []}
            
        except Exception as e:
            print(f"[TopicAgent] Error: {e}")
            # Fallback: Return a generic topic
            return {
                "topics": [{
                    "topic": "Meeting Discussion",
                    "start": segments[0].get('start', 0) if segments else 0,
                    "end": segments[-1].get('end', 0) if segments else 0,
                    "summary": "General discussion covering multiple topics."
                }]
            }
