from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent
from .llm_client import get_mistral_completion


class ActionItemAgent(BaseAgent):
    """
    Extract action items from meeting transcript using Mistral AI.
    Generates professional, well-formatted action items with proper capitalization,
    clear descriptions, assignees, and deadlines.
    """
    name = "action_item_agent"

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.getenv("MISTRAL_API_KEY")

    def _parse_action_items(self, ai_response: str) -> List[Dict[str, Any]]:
        """
        Parse AI-generated action items from structured text format.
        Expected format:
        - Action: [description]
          Assignee: [name]
          Due: [deadline]
        """
        action_items = []
        
        # Split by lines and group action items
        lines = [line.strip() for line in ai_response.split('\n') if line.strip()]
        
        current_item = {}
        for line in lines:
            # Remove leading dash or bullet
            line = re.sub(r'^[-•*]\s*', '', line)
            
            # Check for action
            if line.lower().startswith('action:') or line.lower().startswith('action item'):
                # Save previous item if exists
                if current_item.get('action'):
                    action_items.append(current_item)
                
                # Start new item
                action_text = re.sub(r'^action(?:\s+item)?:\s*', '', line, flags=re.IGNORECASE)
                current_item = {'action': action_text.strip(), 'assignee': None, 'due': None}
            
            # Check for assignee
            elif 'assignee:' in line.lower() or 'assigned to:' in line.lower():
                assignee = re.sub(r'^.*?(?:assignee|assigned to):\s*', '', line, flags=re.IGNORECASE)
                assignee = assignee.strip()
                if assignee and assignee.lower() not in ['none', 'n/a', 'tbd']:
                    current_item['assignee'] = assignee
            
            # Check for due date
            elif 'due:' in line.lower() or 'deadline:' in line.lower():
                due = re.sub(r'^.*?(?:due|deadline):\s*', '', line, flags=re.IGNORECASE)
                due = due.strip()
                if due and due.lower() not in ['none', 'n/a', 'tbd']:
                    current_item['due'] = due
        
        # Add last item
        if current_item.get('action'):
            action_items.append(current_item)
        
        return action_items

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract action items using Mistral AI for professional formatting.
        
        Returns:
            {
                "action_items": [
                    {
                        "action": "Organize Pancake Breakfast",
                        "assignee": "Team",
                        "due": "Next Friday"
                    }
                ]
            }
        """
        text: str = payload.get("text", "")
        segments: list = payload.get("segments", [])
        
        if not text or len(text) < 50:
            return {"action_items": []}
        
        # Truncate if too long
        max_words = 2500
        words = text.split()
        if len(words) > max_words:
            text = ' '.join(words[:max_words]) + "..."
        
        # Create prompt for AI to extract action items
        prompt = f"""You are an expert at analyzing meeting transcripts and extracting action items. Review this meeting transcript and identify all action items, tasks, and commitments.

Transcript:
{text}

Extract all action items from this meeting. For each action item, provide:
1. A clear, professional description of what needs to be done (capitalize properly)
2. Who is responsible (assignee) - use names if mentioned, or "Team" if it's a group task
3. When it's due (if mentioned)

Format each action item EXACTLY like this:
Action: [Clear, professional description]
Assignee: [Name or "Team"]
Due: [Deadline or leave blank]

Guidelines:
- Start each action with a clear verb (Organize, Create, Post, Send, Meet, Research, etc.)
- Use proper capitalization and professional language
- Be specific and actionable
- Only include actual commitments, not general discussions
- If no assignee is mentioned, use "Team"
- If no deadline is mentioned, leave Due blank

Action Items:"""

        try:
            # Get AI-generated action items
            ai_response = await get_mistral_completion(
                prompt=prompt,
                max_tokens=600,
                temperature=0.3,
                api_key=self.token
            )
            
            if not ai_response:
                return {"action_items": []}
            
            # Parse the AI response
            action_items = self._parse_action_items(ai_response)
            
            # Clean up and validate each action item
            cleaned_items = []
            for item in action_items:
                action = item.get('action', '').strip()
                
                # Skip if action is too short or generic
                if len(action) < 10 or action.lower() in ['none', 'n/a']:
                    continue
                
                # Ensure action starts with capital letter
                if action and not action[0].isupper():
                    action = action[0].upper() + action[1:]
                
                # Build clean item
                clean_item = {
                    'action': action,
                    'assignee': item.get('assignee'),
                    'due': item.get('due')
                }
                
                # Try to find timestamp from segments (for the first mention)
                timestamp = None
                action_lower = action.lower()
                for seg in segments:
                    seg_text = seg.get('text', '').lower()
                    # Check if this segment is related to this action
                    action_words = set(action_lower.split()[:5])  # First 5 words
                    seg_words = set(seg_text.split())
                    if len(action_words & seg_words) >= 2:  # At least 2 matching words
                        timestamp = seg.get('start')
                        break
                
                clean_item['timestamp'] = timestamp
                
                # Add evidence (first relevant segment)
                if timestamp is not None:
                    for seg in segments:
                        if seg.get('start') == timestamp:
                            evidence = seg.get('text', '')[:150]
                            clean_item['evidence'] = evidence + "..." if len(seg.get('text', '')) > 150 else evidence
                            break
                
                cleaned_items.append(clean_item)
            
            return {"action_items": cleaned_items}
            
        except Exception as e:
            print(f"[ActionItemAgent] Mistral API error: {e}")
            # Fallback: return empty list
            return {"action_items": []}