from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent


class ActionItemAgent(BaseAgent):
    """
    Extract action items from meeting transcript using pattern matching.
    - Primary: Action verb detection and assignee extraction
    - Fallback: Simple keyword matching
    """
    name = "action_item_agent"

    def __init__(self) -> None:
        self.action_patterns = [
            r"(?:will|should|must|need to|have to)\s+([^.!?]+)",
            r"(?:task|action|todo|assignment):\s*([^.!?]+)",
            r"([A-Z][a-z]+)\s+(?:will|should|needs to)\s+([^.!?]+)",  # Name + action
        ]
        self.deadline_patterns = [
            r"by\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"by\s+(tomorrow|today|next week|this week|end of week)",
            r"(?:due|deadline):\s*([^.!?,]+)",
            r"before\s+([^.!?,]+)",
        ]

    def _extract_deadline(self, text: str) -> Optional[str]:
        """Extract deadline from text using simple patterns."""
        for pattern in self.deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_action_items(self, text: str, segments: List[Dict]) -> List[Dict[str, Any]]:
        """
        Extract action items using pattern matching and verb detection.
        """
        action_items = []
        for seg in segments:
            seg_text = seg.get('text', '')
            
            for pattern in self.action_patterns:
                matches = re.finditer(pattern, seg_text, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) == 2:
                        # Pattern with name
                        assignee = match.group(1)
                        action = match.group(2).strip()
                    else:
                        assignee = None
                        action = match.group(1).strip()
                    
                    if len(action) > 10:  # Filter short matches
                        # Try to extract deadline
                        deadline = self._extract_deadline(seg_text)
                        
                        action_items.append({
                            "action": action,
                            "assignee": assignee,
                            "due": deadline,
                            "timestamp": seg.get('start', 0),
                            "evidence": seg_text[:200]
                        })
        
        return action_items

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract action items with assignees and deadlines.
        
        Returns:
            {
                "action_items": [
                    {
                        "action": "Send proposal to client",
                        "assignee": "John",
                        "due": "Friday",
                        "timestamp": 320.1,
                        "evidence": "John will send..."
                    }
                ]
            }
        """
        text: str = payload.get("text", "")
        segments: list = payload.get("segments", [])
        
        action_items = self._extract_action_items(text, segments)
        
        return {"action_items": action_items}
