from __future__ import annotations

import os
import re
import json
import asyncio
from typing import Any, Dict, List
from dataclasses import dataclass, asdict

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    import requests
    HTTPX_AVAILABLE = False

from .base_agent import BaseAgent


@dataclass
class Decision:
    """Structured decision data."""
    decision: str
    context: str
    impact: str  # "High", "Medium", or "Low"
    participants: List[str]
    timestamp: float | None
    confidence: float
    evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DecisionAgent(BaseAgent):
    """
    Extract decisions made during the meeting.
    - Primary: Groq API for intelligent extraction
    - Fallback: Regex pattern matching
    """
    name = "decision_agent"

    # Groq API configuration
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL = "llama-3.3-70b-versatile"  # Fast and capable model
    GROQ_API_KEY_ENV = "GROQ_API_KEY"  # Changed from GROK_API_KEY

    def __init__(self) -> None:
        # Try GROK_API_KEY if GROQ_API_KEY doesnt work
        self.api_key = os.getenv(self.GROQ_API_KEY_ENV)
        self.use_api = bool(self.api_key)
        
        # Debug output
        if self.api_key:
            print(f"✅ Groq API Key loaded: {self.api_key[:10]}...")
        else:
            print("⚠️  No Groq API key found. Using pattern matching fallback.")
        
        # Fallback regex patterns
        self.decision_patterns = [
            r"(?:we|they|team)\s+(?:decided|agreed|chose|selected)\s+(?:to|on)\s+([^.!?]+)",
            r"(?:decision|agreement|consensus)\s+(?:was|is)\s+(?:to|that)\s+([^.!?]+)",
            r"(?:will|shall|going to)\s+(?:proceed|move forward|implement)\s+(?:with|on)\s+([^.!?]+)",
            r"(?:approved|confirmed|finalized)\s+([^.!?]+)",
        ]

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract decisions with context and participants.
        Returns:
            {
                "decisions": [
                    {
                        "decision": "Proceed with Option A",
                        "context": "Technical discussion during Q2 planning",
                        "impact": "High",
                        "participants": ["SPEAKER_00", "SPEAKER_01"],
                        "timestamp": 245.3,
                        "confidence": 0.9,
                        "evidence": "After discussion, we agreed..."
                    }
                ]
            }
        """
        text: str = payload.get("text", "")
        segments: list = payload.get("segments", [])
        
        if not text and not segments:
            return {"decisions": []}

        # Try Groq API first if available
        if self.use_api:
            try:
                decisions = await self._extract_with_groq(text, segments)
                return {"decisions": decisions}
            except Exception as e:
                print(f"Warning: Groq API decision extraction failed: {e}. Falling back to pattern matching.")
        
        # Fallback to pattern matching
        decisions = self._extract_with_patterns(text, segments)
        return {"decisions": decisions}

    async def _extract_with_groq(self, text: str, segments: List[Dict]) -> List[Dict[str, Any]]:
        """Extract decisions using Groq API."""
        # Build comprehensive transcript with speaker info
        transcript = self._build_transcript(text, segments)
        prompt = self._build_extraction_prompt(transcript)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert at analyzing meeting transcripts and extracting key decisions. Always respond with valid JSON only, no additional text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 3000
        }

        # Use httpx for async if available, otherwise run requests in thread
        if HTTPX_AVAILABLE:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.GROQ_API_URL,
                    headers=headers,
                    json=payload
                )
                
                # Better error handling with response details
                if response.status_code != 200:
                    error_detail = response.text
                    print(f"Groq API Error Details: {error_detail}")
                    response.raise_for_status()
                
                result = response.json()
        else:
            # Fallback to synchronous requests in thread
            def _sync_request():
                response = requests.post(
                    self.GROQ_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                
                # Better error handling with response details
                if response.status_code != 200:
                    error_detail = response.text
                    print(f"Groq API Error Details: {error_detail}")
                    response.raise_for_status()
                
                return response.json()
            
            result = await asyncio.to_thread(_sync_request)

        # Extract content from response
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        
        # Clean markdown code blocks
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Parse and normalize
        return self._parse_groq_response(content)

    def _build_transcript(self, text: str, segments: List[Dict]) -> str:
        """Build a formatted transcript with speaker and timestamp info."""
        if segments:
            lines = []
            for seg in segments:
                speaker = seg.get('speaker', 'Unknown')
                timestamp = seg.get('start', 0)
                seg_text = seg.get('text', '').strip()
                if seg_text:
                    lines.append(f"[{timestamp:.1f}s] {speaker}: {seg_text}")
            return "\n".join(lines)
        return text

    def _build_extraction_prompt(self, transcript: str) -> str:
        """Build the prompt for decision extraction."""
        # Truncate if too long
        max_length = 10000
        if len(transcript) > max_length:
            transcript = "..." + transcript[-max_length:]

        return f"""Analyze the following meeting transcript and extract all key decisions made during the meeting.

For each decision, identify:
1. **decision**: The actual decision statement (what was decided)
2. **context**: When/where in the meeting this decision was discussed
3. **impact**: The impact level - "High" (affects major outcomes/timelines), "Medium" (moderate impact), or "Low" (minor impact)
4. **participants**: List of speaker names/identifiers involved in this decision
5. **timestamp**: Approximate time in seconds when this decision was made (if available, otherwise null)
6. **confidence**: Your confidence in this extraction (0.0 to 1.0)
7. **evidence**: A brief excerpt from the transcript supporting this decision

Return ONLY a JSON object with this exact structure:
{{
  "decisions": [
    {{
      "decision": "Decision statement here",
      "context": "Context description",
      "impact": "High|Medium|Low",
      "participants": ["Speaker1", "Speaker2"],
      "timestamp": 123.5,
      "confidence": 0.9,
      "evidence": "Brief excerpt from transcript"
    }}
  ]
}}

Transcript:
{transcript}

JSON Response:"""

    def _parse_groq_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse and normalize Groq API response."""
        try:
            parsed = json.loads(content)
            decisions_data = parsed.get("decisions", [])
            
            normalized = []
            for decision_item in decisions_data:
                # Handle participants (list or comma-separated string)
                participants = decision_item.get("participants", [])
                if isinstance(participants, str):
                    participants = [p.strip() for p in participants.split(",")]
                elif not isinstance(participants, list):
                    participants = []
                
                # Normalize impact level
                impact = str(decision_item.get("impact", "Medium")).capitalize()
                if impact not in ["High", "Medium", "Low"]:
                    impact = "Medium"
                
                # Get timestamp
                timestamp = decision_item.get("timestamp")
                if timestamp is not None:
                    try:
                        timestamp = float(timestamp)
                    except (ValueError, TypeError):
                        timestamp = None
                
                # Create normalized decision
                normalized_decision = Decision(
                    decision=decision_item.get("decision", "") or decision_item.get("text", ""),
                    context=decision_item.get("context", ""),
                    impact=impact,
                    participants=participants,
                    timestamp=timestamp,
                    confidence=float(decision_item.get("confidence", 0.8)),
                    evidence=decision_item.get("evidence", "")[:200]  # Truncate evidence
                )
                normalized.append(normalized_decision.to_dict())
            
            return normalized
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Groq API JSON response: {e}")

    def _extract_with_patterns(self, text: str, segments: List[Dict]) -> List[Dict[str, Any]]:
        """
        Fallback: Extract decisions using regex pattern matching.
        """
        decisions = []
        
        for seg in segments:
            seg_text = seg.get('text', '')
            speaker = seg.get('speaker', 'Unknown')
            timestamp = seg.get('start', 0)
            
            for pattern in self.decision_patterns:
                matches = re.finditer(pattern, seg_text, re.IGNORECASE)
                for match in matches:
                    decision_text = match.group(1).strip()
                    if len(decision_text) > 10:  # Filter short matches
                        decision = Decision(
                            decision=decision_text,
                            context="Detected via pattern matching",
                            impact="Medium",  # Default
                            participants=[speaker],
                            timestamp=timestamp,
                            confidence=0.5,  # Lower confidence for pattern matching
                            evidence=seg_text[:200]
                        )
                        decisions.append(decision.to_dict())
        
        return decisions