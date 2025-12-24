from __future__ import annotations

import re
from typing import Any, Dict, List

from .base_agent import BaseAgent


class DecisionAgent(BaseAgent):
    """
    Extract decisions made during the meeting using pattern matching.
    - Primary: Regex patterns for decision phrases
    - Fallback: Simple keyword detection
    """
    name = "decision_agent"

    def __init__(self) -> None:
        self.decision_patterns = [
            r"(?:we|they|team)\s+(?:decided|agreed|chose|selected)\s+(?:to|on)\s+([^.!?]+)",
            r"(?:decision|agreement|consensus)\s+(?:was|is)\s+(?:to|that)\s+([^.!?]+)",
            r"(?:will|shall|going to)\s+(?:proceed|move forward|implement)\s+(?:with|on)\s+([^.!?]+)",
            r"(?:approved|confirmed|finalized)\s+([^.!?]+)",
        ]

    def _extract_decisions(self, text: str, segments: List[Dict]) -> List[Dict[str, Any]]:
        """
        Extract decisions using pattern matching.
        Robust fallback method.
        """
        decisions = []
        for seg in segments:
            seg_text = seg.get('text', '')
            speaker = seg.get('speaker', 'Unknown')
            
            for pattern in self.decision_patterns:
                matches = re.finditer(pattern, seg_text, re.IGNORECASE)
                for match in matches:
                    decision_text = match.group(1).strip()
                    if len(decision_text) > 10:  # Filter out too short matches
                        decisions.append({
                            "decision": decision_text,
                            "participants": [speaker],
                            "timestamp": seg.get('start', 0),
                            "evidence": seg_text[:200]
                        })
        
        return decisions

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract decisions with context and participants.
        
        Returns:
            {
                "decisions": [
                    {
                        "decision": "Proceed with Option A",
                        "participants": ["SPEAKER_00"],
                        "timestamp": 245.3,
                        "evidence": "After discussion, we agreed..."
                    }
                ]
            }
        """
        text: str = payload.get("text", "")
        segments: list = payload.get("segments", [])
        
        decisions = self._extract_decisions(text, segments)
        
        return {"decisions": decisions}
