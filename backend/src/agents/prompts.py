TOPIC_SYSTEM = "You segment meetings into coherent topics with timestamps."
TOPIC_PROMPT = """
Given a meeting transcript, identify topic segments.
Return JSON with fields: topic (string), start (seconds), end (seconds), summary (string).
Keep 3-10 topics depending on length.
"""

DECISION_SYSTEM = "You extract decisions from meetings with participants and rationale."
DECISION_PROMPT = """
Extract decisions from the meeting transcript.
Return JSON list of objects: decision (string), participants (array of strings), rationale (string), evidence (short quote).
Only include clear decisions; omit speculative statements.
"""

ACTION_SYSTEM = "You extract actionable tasks from meetings."
ACTION_PROMPT = """
Extract action items from the meeting transcript.
Return JSON list of objects: action (string), assignee (string or null), due (string or null), evidence (short quote).
Prefer explicit assignments; if no assignee/due, set to null.
"""

SENTIMENT_SYSTEM = "You assess sentiment per segment."
SENTIMENT_PROMPT = """
Classify sentiment for each segment as one of [positive, neutral, negative] and give a brief rationale.
Return JSON list of objects: sentiment (string), rationale (string), start (seconds), end (seconds), text (string).
"""

SUMMARY_SYSTEM = "You summarize meetings concisely."
SUMMARY_PROMPT = """
Provide a concise bullet summary under 120 words. Include key decisions and action items if present.
Return plain text bullets.
"""

