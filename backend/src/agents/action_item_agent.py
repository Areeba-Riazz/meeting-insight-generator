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
            
            # Check for action - more flexible matching
            if re.search(r'^action\s*(?:item)?[\s:]', line, re.IGNORECASE):
                # Save previous item if exists
                if current_item.get('action'):
                    action_items.append(current_item)
                
                # Start new item - handle both "Action:" and "Action -" formats
                action_text = re.sub(r'^action(?:\s+item)?[\s:-]*', '', line, flags=re.IGNORECASE)
                current_item = {'action': action_text.strip(), 'assignee': None, 'due': None}
            
            # Check for assignee
            elif re.search(r'(?:assignee|assigned to)[\s:]', line, re.IGNORECASE):
                assignee = re.sub(r'^.*?(?:assignee|assigned to)[\s:-]*', '', line, flags=re.IGNORECASE)
                assignee = assignee.strip()
                if assignee and assignee.lower() not in ['none', 'n/a', 'tbd', '']:
                    current_item['assignee'] = assignee
            
            # Check for due date
            elif re.search(r'(?:due|deadline|when|by)[\s:]', line, re.IGNORECASE):
                due = re.sub(r'^.*?(?:due|deadline|when|by)[\s:-]*', '', line, flags=re.IGNORECASE)
                due = due.strip()
                if due and due.lower() not in ['none', 'n/a', 'tbd', '']:
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
- Action: [Clear, professional description]
  Assignee: [Name or "Team"]
  Due: [Deadline or leave blank]

Guidelines:
- Start each action with a clear verb (Organize, Create, Post, Send, Meet, Research, etc.)
- Use proper capitalization and professional language
- Be specific and actionable
- Only include actual commitments, not general discussions
- If no assignee is mentioned, use "Team"
- If no deadline is mentioned, leave Due blank
- Include all action items mentioned in the meeting

List all action items below:"""

        try:
            # Get AI-generated action items
            ai_response = await get_mistral_completion(
                prompt=prompt,
                max_tokens=800,
                temperature=0.3,
                api_key=self.token
            )
            
            if not ai_response:
                print("[ActionItemAgent] No response from Mistral API")
                return {"action_items": []}
            
            # Parse the AI response
            action_items = self._parse_action_items(ai_response)
            
            # If no items were parsed, try a more lenient approach
            if not action_items:
                print(f"[ActionItemAgent] No structured items found in response, trying fallback parsing")
                print(f"[ActionItemAgent] Raw AI response: {ai_response[:500]}")
                action_items = self._fallback_extract_action_items(ai_response, text)
            
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
            # Fallback: try simple keyword extraction
            return self._fallback_keyword_extraction(text, segments)
    
    def _fallback_extract_action_items(self, ai_response: str, transcript: str) -> List[Dict[str, Any]]:
        """Fallback parsing when structured format fails."""
        action_items = []
        
        # Look for common action item patterns in the response
        # Pattern 1: Lines starting with bullet points or numbers
        lines = ai_response.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Remove bullets, numbers, etc.
            cleaned = re.sub(r'^[-•*\d+.)\s]+', '', line)
            
            # Skip if looks like a header or instruction
            if any(keyword in cleaned.lower() for keyword in ['action item', 'extract', 'below:', 'list']):
                continue
            
            # If line contains common action keywords
            if any(verb in cleaned.lower() for verb in ['organize', 'create', 'send', 'post', 'meet', 'research', 'prepare', 'plan', 'develop', 'implement', 'conduct', 'discuss', 'review', 'provide', 'arrange', 'schedule', 'contact', 'follow up', 'update']):
                if len(cleaned) > 10:
                    action_items.append({'action': cleaned, 'assignee': None, 'due': None})
        
        return action_items
    
    def _fallback_keyword_extraction(self, transcript: str, segments: list) -> Dict[str, Any]:
        """Last resort: extract action items based on keywords and patterns."""
        action_items = []
        action_keywords = [
            'organize', 'create', 'send', 'post', 'meet', 'research', 'prepare', 'plan',
            'develop', 'implement', 'conduct', 'discuss', 'review', 'provide', 'arrange',
            'schedule', 'contact', 'follow up', 'should', 'will do', 'need to', 'got to'
        ]
        
        # Find sentences with action keywords
        sentences = re.split(r'[.!?]\s+', transcript)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 20:
                continue
            
            # Check if sentence contains action keywords
            if any(keyword in sentence.lower() for keyword in action_keywords):
                # Extract action
                action = sentence[:100].strip()
                
                # Try to extract assignee
                assignee = None
                if re.search(r'\b(?:by|assigned to|for)\s+([A-Z][a-z]+)', sentence):
                    match = re.search(r'\b(?:by|assigned to|for)\s+([A-Z][a-z]+)', sentence)
                    if match:
                        assignee = match.group(1)
                
                item = {'action': action, 'assignee': assignee, 'due': None}
                action_items.append(item)
        
        # Remove duplicates
        unique_items = []
        seen = set()
        for item in action_items:
            key = item['action'].lower()[:50]
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        return {"action_items": unique_items[:5]}