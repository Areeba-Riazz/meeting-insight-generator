"""Database models for PostgreSQL."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Project(Base):
    """Project model - stores project information."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    meetings: Mapped[List["Meeting"]] = relationship(
        "Meeting",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name})>"


class Meeting(Base):
    """Meeting model - stores meeting metadata."""

    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    meeting_name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    transcript_path: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )
    diarized_transcript_path: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="uploading",
        index=True,
    )
    upload_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        index=True,
    )
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="meetings")
    transcript: Mapped[Optional["Transcript"]] = relationship(
        "Transcript",
        back_populates="meeting",
        uselist=False,
        cascade="all, delete-orphan",
    )
    topics: Mapped[List["Topic"]] = relationship(
        "Topic",
        back_populates="meeting",
        cascade="all, delete-orphan",
    )
    decisions: Mapped[List["Decision"]] = relationship(
        "Decision",
        back_populates="meeting",
        cascade="all, delete-orphan",
    )
    action_items: Mapped[List["ActionItem"]] = relationship(
        "ActionItem",
        back_populates="meeting",
        cascade="all, delete-orphan",
    )
    sentiment_analysis: Mapped[Optional["SentimentAnalysis"]] = relationship(
        "SentimentAnalysis",
        back_populates="meeting",
        uselist=False,
        cascade="all, delete-orphan",
    )
    summary: Mapped[Optional["Summary"]] = relationship(
        "Summary",
        back_populates="meeting",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_meeting_project_upload", "project_id", "upload_timestamp"),
    )

    def __repr__(self) -> str:
        return f"<Meeting(id={self.id}, name={self.meeting_name}, status={self.status})>"


class Transcript(Base):
    """Transcript model - stores transcript data."""

    __tablename__ = "transcripts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # Relationships
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="transcript")
    segments: Mapped[List["TranscriptSegment"]] = relationship(
        "TranscriptSegment",
        back_populates="transcript",
        cascade="all, delete-orphan",
        order_by="TranscriptSegment.segment_index",
    )

    def __repr__(self) -> str:
        return f"<Transcript(id={self.id}, meeting_id={self.meeting_id})>"


class TranscriptSegment(Base):
    """Transcript segment model - stores individual transcript segments."""

    __tablename__ = "transcript_segments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    transcript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    end: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    speaker: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    segment_index: Mapped[int] = mapped_column(nullable=False)

    # Relationships
    transcript: Mapped["Transcript"] = relationship(
        "Transcript", back_populates="segments"
    )

    # Indexes
    __table_args__ = (
        Index("idx_segment_transcript_index", "transcript_id", "segment_index"),
        Index("idx_segment_speaker", "speaker"),
        CheckConstraint('start < "end"', name="check_start_before_end"),
    )

    def __repr__(self) -> str:
        return f"<TranscriptSegment(id={self.id}, index={self.segment_index})>"


class Topic(Base):
    """Topic model - stores topics extracted from meetings."""

    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_time: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 3), nullable=True
    )
    end_time: Mapped[Optional[float]] = mapped_column(Numeric(10, 3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # Relationships
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="topics")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "start_time IS NULL OR end_time IS NULL OR start_time < end_time",
            name="check_topic_time_range",
        ),
    )

    def __repr__(self) -> str:
        return f"<Topic(id={self.id}, topic={self.topic[:50]})>"


class Decision(Base):
    """Decision model - stores decisions made during meetings."""

    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    participants: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # Relationships
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="decisions")

    # Indexes
    __table_args__ = (
        Index("idx_decision_participants", "participants", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<Decision(id={self.id}, decision={self.decision[:50]})>"


class ActionItem(Base):
    """Action item model - stores action items extracted from meetings."""

    __tablename__ = "action_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(Text, nullable=False)
    assignee: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # Relationships
    meeting: Mapped["Meeting"] = relationship(
        "Meeting", back_populates="action_items"
    )

    # Indexes
    __table_args__ = (
        Index("idx_action_assignee", "assignee"),
        Index("idx_action_status", "status"),
        Index("idx_action_due_date", "due_date"),
    )

    def __repr__(self) -> str:
        return f"<ActionItem(id={self.id}, action={self.action[:50]})>"


class SentimentAnalysis(Base):
    """Sentiment analysis model - stores overall sentiment analysis."""

    __tablename__ = "sentiment_analysis"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    overall_sentiment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    overall_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 3), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # Relationships
    meeting: Mapped["Meeting"] = relationship(
        "Meeting", back_populates="sentiment_analysis"
    )
    segments: Mapped[List["SentimentSegment"]] = relationship(
        "SentimentSegment",
        back_populates="sentiment_analysis",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "overall_score IS NULL OR (overall_score >= -1 AND overall_score <= 1)",
            name="check_sentiment_score_range",
        ),
    )

    def __repr__(self) -> str:
        return f"<SentimentAnalysis(id={self.id}, meeting_id={self.meeting_id})>"


class SentimentSegment(Base):
    """Sentiment segment model - stores sentiment for individual segments."""

    __tablename__ = "sentiment_segments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    sentiment_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sentiment_analysis.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_text: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(5, 3), nullable=False)
    start_time: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 3), nullable=True
    )
    end_time: Mapped[Optional[float]] = mapped_column(Numeric(10, 3), nullable=True)

    # Relationships
    sentiment_analysis: Mapped["SentimentAnalysis"] = relationship(
        "SentimentAnalysis", back_populates="segments"
    )

    # Indexes
    __table_args__ = (
        Index("idx_sentiment_segment_sentiment", "sentiment"),
        CheckConstraint(
            "score >= -1 AND score <= 1", name="check_sentiment_segment_score_range"
        ),
    )

    def __repr__(self) -> str:
        return f"<SentimentSegment(id={self.id}, sentiment={self.sentiment})>"


class Summary(Base):
    """Summary model - stores meeting summaries."""

    __tablename__ = "summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # Relationships
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="summary")

    def __repr__(self) -> str:
        return f"<Summary(id={self.id}, meeting_id={self.meeting_id})>"

