"""Database service layer for database operations."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_models import (
    Project,
    Meeting,
    Transcript,
    TranscriptSegment,
    Topic,
    Decision,
    ActionItem,
    SentimentAnalysis,
    SentimentSegment,
    Summary,
)


class DatabaseService:
    """Service class for database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    # ========== Project Methods ==========

    async def create_project(
        self, name: str, description: Optional[str] = None
    ) -> Project:
        """Create a new project."""
        project = Project(name=name, description=description)
        self.session.add(project)
        await self.session.flush()
        await self.session.refresh(project)
        return project

    async def get_project(self, project_id: uuid.UUID) -> Optional[Project]:
        """Get project by ID."""
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def list_projects(
        self, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        """List all projects with pagination."""
        result = await self.session.execute(
            select(Project)
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_projects(self) -> int:
        """Count total number of projects."""
        result = await self.session.execute(select(func.count(Project.id)))
        return result.scalar() or 0

    async def update_project(
        self,
        project_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Project]:
        """Update project."""
        project = await self.get_project(project_id)
        if not project:
            return None

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        project.updated_at = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(project)
        return project

    async def delete_project(self, project_id: uuid.UUID) -> bool:
        """Delete project (cascades to meetings)."""
        project = await self.get_project(project_id)
        if not project:
            return False

        await self.session.delete(project)
        await self.session.flush()
        return True

    # ========== Meeting Methods ==========

    async def create_meeting(
        self,
        project_id: uuid.UUID,
        meeting_name: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        content_type: Optional[str] = None,
    ) -> Meeting:
        """Create a new meeting."""
        meeting = Meeting(
            project_id=project_id,
            meeting_name=meeting_name,
            original_filename=original_filename,
            file_path=file_path,
            file_size_bytes=file_size,
            content_type=content_type,
            status="uploading",
        )
        self.session.add(meeting)
        await self.session.flush()
        await self.session.refresh(meeting)
        return meeting

    async def get_meeting(self, meeting_id: uuid.UUID) -> Optional[Meeting]:
        """Get meeting by ID."""
        result = await self.session.execute(
            select(Meeting).where(Meeting.id == meeting_id)
        )
        return result.scalar_one_or_none()

    async def get_meetings_by_project(
        self, project_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Meeting]:
        """Get all meetings for a project."""
        result = await self.session.execute(
            select(Meeting)
            .where(Meeting.project_id == project_id)
            .order_by(Meeting.upload_timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_meetings_by_project(self, project_id: uuid.UUID) -> int:
        """Count meetings for a project."""
        result = await self.session.execute(
            select(func.count(Meeting.id)).where(Meeting.project_id == project_id)
        )
        return result.scalar() or 0

    async def update_meeting_status(
        self, meeting_id: uuid.UUID, status: str
    ) -> Optional[Meeting]:
        """Update meeting status."""
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            return None

        meeting.status = status
        if status == "completed":
            meeting.processing_completed_at = datetime.utcnow()

        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(meeting)
        return meeting

    async def update_meeting_paths(
        self,
        meeting_id: uuid.UUID,
        transcript_path: Optional[str] = None,
        diarized_transcript_path: Optional[str] = None,
    ) -> Optional[Meeting]:
        """Update meeting file paths."""
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            return None

        if transcript_path is not None:
            meeting.transcript_path = transcript_path
        if diarized_transcript_path is not None:
            meeting.diarized_transcript_path = diarized_transcript_path

        await self.session.flush()
        await self.session.refresh(meeting)
        return meeting

    async def delete_meeting(self, meeting_id: uuid.UUID) -> bool:
        """Delete meeting (cascades to insights)."""
        meeting = await self.get_meeting(meeting_id)
        if not meeting:
            return False

        await self.session.delete(meeting)
        await self.session.flush()
        return True

    async def list_all_meetings(
        self, skip: int = 0, limit: int = 100
    ) -> List[Meeting]:
        """List all meetings across all projects."""
        result = await self.session.execute(
            select(Meeting)
            .order_by(Meeting.upload_timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ========== Transcript Methods ==========

    async def save_transcript(
        self, meeting_id: uuid.UUID, text: str, model: Optional[str] = None
    ) -> Transcript:
        """Save transcript for a meeting."""
        transcript = Transcript(meeting_id=meeting_id, text=text, model=model)
        self.session.add(transcript)
        await self.session.flush()
        await self.session.refresh(transcript)
        return transcript

    async def get_transcript(self, meeting_id: uuid.UUID) -> Optional[Transcript]:
        """Get transcript for a meeting."""
        result = await self.session.execute(
            select(Transcript).where(Transcript.meeting_id == meeting_id)
        )
        return result.scalar_one_or_none()

    async def save_transcript_segments(
        self, transcript_id: uuid.UUID, segments: List[Dict]
    ) -> List[TranscriptSegment]:
        """Save transcript segments."""
        segment_objects = []
        for idx, seg in enumerate(segments):
            segment = TranscriptSegment(
                transcript_id=transcript_id,
                text=seg.get("text", ""),
                start=float(seg.get("start", 0)),
                end=float(seg.get("end", 0)),
                speaker=seg.get("speaker"),
                segment_index=idx,
            )
            segment_objects.append(segment)
            self.session.add(segment)

        await self.session.flush()
        return segment_objects

    async def get_transcript_segments(
        self, transcript_id: uuid.UUID
    ) -> List[TranscriptSegment]:
        """Get all segments for a transcript."""
        result = await self.session.execute(
            select(TranscriptSegment)
            .where(TranscriptSegment.transcript_id == transcript_id)
            .order_by(TranscriptSegment.segment_index)
        )
        return list(result.scalars().all())

    # ========== Topic Methods ==========

    async def save_topics(
        self, meeting_id: uuid.UUID, topics: List[Dict]
    ) -> List[Topic]:
        """Save topics for a meeting."""
        topic_objects = []
        for topic_data in topics:
            topic = Topic(
                meeting_id=meeting_id,
                topic=topic_data.get("topic", ""),
                summary=topic_data.get("summary"),
                start_time=(
                    float(topic_data["start"]) if topic_data.get("start") else None
                ),
                end_time=(float(topic_data["end"]) if topic_data.get("end") else None),
            )
            topic_objects.append(topic)
            self.session.add(topic)

        await self.session.flush()
        return topic_objects

    async def get_topics(self, meeting_id: uuid.UUID) -> List[Topic]:
        """Get all topics for a meeting."""
        result = await self.session.execute(
            select(Topic).where(Topic.meeting_id == meeting_id)
        )
        return list(result.scalars().all())

    async def delete_topics(self, meeting_id: uuid.UUID) -> bool:
        """Delete all topics for a meeting."""
        result = await self.session.execute(
            select(Topic).where(Topic.meeting_id == meeting_id)
        )
        topics = result.scalars().all()
        for topic in topics:
            await self.session.delete(topic)
        await self.session.flush()
        return True

    # ========== Decision Methods ==========

    async def save_decisions(
        self, meeting_id: uuid.UUID, decisions: List[Dict]
    ) -> List[Decision]:
        """Save decisions for a meeting."""
        decision_objects = []
        for decision_data in decisions:
            decision = Decision(
                meeting_id=meeting_id,
                decision=decision_data.get("decision", ""),
                participants=decision_data.get("participants"),
                rationale=decision_data.get("rationale"),
                evidence=decision_data.get("evidence"),
            )
            decision_objects.append(decision)
            self.session.add(decision)

        await self.session.flush()
        return decision_objects

    async def get_decisions(self, meeting_id: uuid.UUID) -> List[Decision]:
        """Get all decisions for a meeting."""
        result = await self.session.execute(
            select(Decision).where(Decision.meeting_id == meeting_id)
        )
        return list(result.scalars().all())

    async def delete_decisions(self, meeting_id: uuid.UUID) -> bool:
        """Delete all decisions for a meeting."""
        result = await self.session.execute(
            select(Decision).where(Decision.meeting_id == meeting_id)
        )
        decisions = result.scalars().all()
        for decision in decisions:
            await self.session.delete(decision)
        await self.session.flush()
        return True

    # ========== Action Item Methods ==========

    async def save_action_items(
        self, meeting_id: uuid.UUID, action_items: List[Dict]
    ) -> List[ActionItem]:
        """Save action items for a meeting."""
        action_item_objects = []
        for item_data in action_items:
            due_date = None
            if item_data.get("due"):
                try:
                    due_date = datetime.fromisoformat(item_data["due"].replace("Z", "+00:00")).date()
                except (ValueError, AttributeError):
                    pass

            action_item = ActionItem(
                meeting_id=meeting_id,
                action=item_data.get("action", ""),
                assignee=item_data.get("assignee"),
                due_date=due_date,
                evidence=item_data.get("evidence"),
                status=item_data.get("status", "pending"),
            )
            action_item_objects.append(action_item)
            self.session.add(action_item)

        await self.session.flush()
        return action_item_objects

    async def get_action_items(self, meeting_id: uuid.UUID) -> List[ActionItem]:
        """Get all action items for a meeting."""
        result = await self.session.execute(
            select(ActionItem).where(ActionItem.meeting_id == meeting_id)
        )
        return list(result.scalars().all())

    async def update_action_item_status(
        self, action_item_id: uuid.UUID, status: str
    ) -> Optional[ActionItem]:
        """Update action item status."""
        result = await self.session.execute(
            select(ActionItem).where(ActionItem.id == action_item_id)
        )
        action_item = result.scalar_one_or_none()
        if not action_item:
            return None

        action_item.status = status
        await self.session.flush()
        await self.session.refresh(action_item)
        return action_item

    async def delete_action_items(self, meeting_id: uuid.UUID) -> bool:
        """Delete all action items for a meeting."""
        result = await self.session.execute(
            select(ActionItem).where(ActionItem.meeting_id == meeting_id)
        )
        action_items = result.scalars().all()
        for action_item in action_items:
            await self.session.delete(action_item)
        await self.session.flush()
        return True

    # ========== Sentiment Methods ==========

    async def save_sentiment_analysis(
        self,
        meeting_id: uuid.UUID,
        overall_sentiment: Optional[str] = None,
        overall_score: Optional[float] = None,
    ) -> SentimentAnalysis:
        """Save sentiment analysis for a meeting."""
        sentiment = SentimentAnalysis(
            meeting_id=meeting_id,
            overall_sentiment=overall_sentiment,
            overall_score=overall_score,
        )
        self.session.add(sentiment)
        await self.session.flush()
        await self.session.refresh(sentiment)
        return sentiment

    async def get_sentiment_analysis(
        self, meeting_id: uuid.UUID
    ) -> Optional[SentimentAnalysis]:
        """Get sentiment analysis for a meeting."""
        result = await self.session.execute(
            select(SentimentAnalysis).where(
                SentimentAnalysis.meeting_id == meeting_id
            )
        )
        return result.scalar_one_or_none()

    async def save_sentiment_segments(
        self, sentiment_analysis_id: uuid.UUID, segments: List[Dict]
    ) -> List[SentimentSegment]:
        """Save sentiment segments."""
        segment_objects = []
        for seg_data in segments:
            segment = SentimentSegment(
                sentiment_analysis_id=sentiment_analysis_id,
                segment_text=seg_data.get("text", ""),
                sentiment=seg_data.get("sentiment", ""),
                score=float(seg_data.get("score", 0)),
                start_time=(
                    float(seg_data["start"]) if seg_data.get("start") else None
                ),
                end_time=(float(seg_data["end"]) if seg_data.get("end") else None),
            )
            segment_objects.append(segment)
            self.session.add(segment)

        await self.session.flush()
        return segment_objects

    async def get_sentiment_segments(
        self, sentiment_analysis_id: uuid.UUID
    ) -> List[SentimentSegment]:
        """Get all sentiment segments for an analysis."""
        result = await self.session.execute(
            select(SentimentSegment).where(
                SentimentSegment.sentiment_analysis_id == sentiment_analysis_id
            )
        )
        return list(result.scalars().all())

    # ========== Summary Methods ==========

    async def save_summary(
        self, meeting_id: uuid.UUID, summary_text: str | dict
    ) -> Summary:
        """Save summary for a meeting."""
        import json
        # Convert dict to JSON string if necessary
        if isinstance(summary_text, dict):
            summary_text = json.dumps(summary_text)
        summary = Summary(meeting_id=meeting_id, summary_text=summary_text)
        self.session.add(summary)
        await self.session.flush()
        await self.session.refresh(summary)
        return summary

    async def get_summary(self, meeting_id: uuid.UUID) -> Optional[Summary]:
        """Get summary for a meeting."""
        result = await self.session.execute(
            select(Summary).where(Summary.meeting_id == meeting_id)
        )
        return result.scalar_one_or_none()

    async def delete_summary(self, meeting_id: uuid.UUID) -> bool:
        """Delete summary for a meeting."""
        summary = await self.get_summary(meeting_id)
        if not summary:
            return False

        await self.session.delete(summary)
        await self.session.flush()
        return True

    # ========== Complete Insights Methods ==========

    async def save_all_insights(
        self, meeting_id: uuid.UUID, insights_data: Dict
    ) -> Dict:
        """Save all insights for a meeting."""
        saved = {}

        # Save transcript
        transcript_data = insights_data.get("transcript", {})
        if transcript_data:
            transcript = await self.save_transcript(
                meeting_id=meeting_id,
                text=transcript_data.get("text", ""),
                model=transcript_data.get("model"),
            )
            saved["transcript"] = transcript

            # Save transcript segments
            segments = transcript_data.get("segments", [])
            if segments:
                saved_segments = await self.save_transcript_segments(
                    transcript.id, segments
                )
                saved["transcript_segments"] = saved_segments

        # Save topics
        topics = insights_data.get("topics", [])
        if topics:
            saved["topics"] = await self.save_topics(meeting_id, topics)

        # Save decisions
        decisions = insights_data.get("decisions", [])
        if decisions:
            saved["decisions"] = await self.save_decisions(meeting_id, decisions)

        # Save action items
        action_items = insights_data.get("action_items", [])
        if action_items:
            saved["action_items"] = await self.save_action_items(
                meeting_id, action_items
            )

        # Save sentiment
        sentiment_data = insights_data.get("sentiment", {})
        if sentiment_data:
            sentiment = await self.save_sentiment_analysis(
                meeting_id=meeting_id,
                overall_sentiment=sentiment_data.get("overall"),
                overall_score=sentiment_data.get("score"),
            )
            saved["sentiment"] = sentiment

            # Save sentiment segments
            sentiment_segments = sentiment_data.get("segments", [])
            if sentiment_segments:
                saved["sentiment_segments"] = await self.save_sentiment_segments(
                    sentiment.id, sentiment_segments
                )

        # Save summary
        summary_text = insights_data.get("summary", "")
        if summary_text:
            saved["summary"] = await self.save_summary(meeting_id, summary_text)

        return saved

    async def get_all_insights(self, meeting_id: uuid.UUID) -> Dict:
        """Get all insights for a meeting as structured data."""
        insights = {}

        # Get transcript
        transcript = await self.get_transcript(meeting_id)
        if transcript:
            segments = await self.get_transcript_segments(transcript.id)
            insights["transcript"] = {
                "text": transcript.text,
                "model": transcript.model,
                "segments": [
                    {
                        "text": seg.text,
                        "start": float(seg.start),
                        "end": float(seg.end),
                        "speaker": seg.speaker,
                    }
                    for seg in segments
                ],
            }

        # Get topics
        topics = await self.get_topics(meeting_id)
        if topics:
            insights["topics"] = [
                {
                    "topic": topic.topic,
                    "summary": topic.summary,
                    "start": float(topic.start_time) if topic.start_time else None,
                    "end": float(topic.end_time) if topic.end_time else None,
                }
                for topic in topics
            ]

        # Get decisions
        decisions = await self.get_decisions(meeting_id)
        if decisions:
            insights["decisions"] = [
                {
                    "decision": decision.decision,
                    "participants": decision.participants,
                    "rationale": decision.rationale,
                    "evidence": decision.evidence,
                }
                for decision in decisions
            ]

        # Get action items
        action_items = await self.get_action_items(meeting_id)
        if action_items:
            insights["action_items"] = [
                {
                    "action": item.action,
                    "assignee": item.assignee,
                    "due": item.due_date.isoformat() if item.due_date else None,
                    "evidence": item.evidence,
                    "status": item.status,
                }
                for item in action_items
            ]

        # Get sentiment
        sentiment = await self.get_sentiment_analysis(meeting_id)
        if sentiment:
            segments = await self.get_sentiment_segments(sentiment.id)
            insights["sentiment"] = {
                "overall": sentiment.overall_sentiment,
                "score": float(sentiment.overall_score)
                if sentiment.overall_score
                else None,
                "segments": [
                    {
                        "sentiment": seg.sentiment,
                        "score": float(seg.score),
                        "text": seg.segment_text,
                        "start": float(seg.start_time) if seg.start_time else None,
                        "end": float(seg.end_time) if seg.end_time else None,
                    }
                    for seg in segments
                ],
            }

        # Get summary
        summary = await self.get_summary(meeting_id)
        if summary:
            import json
            # Parse JSON string back to dict if it's a JSON string
            summary_text = summary.summary_text
            if isinstance(summary_text, str):
                try:
                    # Try to parse as JSON
                    insights["summary"] = json.loads(summary_text)
                except (json.JSONDecodeError, TypeError):
                    # If it's not valid JSON, treat as plain string
                    insights["summary"] = summary_text
            else:
                insights["summary"] = summary_text

        return insights

