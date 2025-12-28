"""Unit tests for database service."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.database_service import DatabaseService
from src.models.db_models import (
    Project, Meeting, Transcript, Topic, Decision, ActionItem,
    SentimentAnalysis, Summary
)


@pytest.fixture
def mock_session():
    """Create a mock async database session."""
    session = MagicMock()
    session.add = MagicMock()
    session.delete = AsyncMock()  # delete is awaited in the code
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()  # Added commit mock
    return session


@pytest.fixture
def db_service(mock_session):
    """Create a DatabaseService instance for testing."""
    return DatabaseService(mock_session)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_project(db_service, mock_session):
    """Test creating a project."""
    mock_project = Project(id=uuid.uuid4(), name="Test Project", description="Test")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    with patch('src.services.database_service.Project', return_value=mock_project):
        result = await db_service.create_project("Test Project", "Test description")
        
        assert result == mock_project
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_project(db_service, mock_session):
    """Test getting a project by ID."""
    project_id = uuid.uuid4()
    mock_project = Project(id=project_id, name="Test Project")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_project
    mock_session.execute.return_value = mock_result
    
    result = await db_service.get_project(project_id)
    
    assert result == mock_project
    mock_session.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_project_not_found(db_service, mock_session):
    """Test getting a non-existent project."""
    project_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    result = await db_service.get_project(project_id)
    
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_projects(db_service, mock_session):
    """Test listing projects."""
    mock_projects = [
        Project(id=uuid.uuid4(), name="Project 1"),
        Project(id=uuid.uuid4(), name="Project 2"),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_projects
    mock_session.execute.return_value = mock_result
    
    result = await db_service.list_projects(skip=0, limit=10)
    
    assert len(result) == 2
    assert result == mock_projects
    mock_session.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_count_projects(db_service, mock_session):
    """Test counting projects."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = 5
    mock_session.execute.return_value = mock_result
    
    result = await db_service.count_projects()
    
    assert result == 5
    mock_session.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_project(db_service, mock_session):
    """Test updating a project."""
    project_id = uuid.uuid4()
    mock_project = Project(id=project_id, name="Old Name", description="Old Desc")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_project
    mock_session.execute.return_value = mock_result
    
    result = await db_service.update_project(project_id, name="New Name")
    
    assert result == mock_project
    assert mock_project.name == "New Name"
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_project_not_found(db_service, mock_session):
    """Test updating a non-existent project."""
    project_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    result = await db_service.update_project(project_id, name="New Name")
    
    assert result is None
    mock_session.flush.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_project(db_service, mock_session):
    """Test deleting a project."""
    project_id = uuid.uuid4()
    mock_project = Project(id=project_id, name="Test Project")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_project
    mock_session.execute.return_value = mock_result
    
    result = await db_service.delete_project(project_id)
    
    assert result is True
    mock_session.delete.assert_called_once_with(mock_project)
    mock_session.flush.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_project_not_found(db_service, mock_session):
    """Test deleting a non-existent project."""
    project_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    result = await db_service.delete_project(project_id)
    
    assert result is False
    mock_session.delete.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_meeting(db_service, mock_session):
    """Test creating a meeting."""
    project_id = uuid.uuid4()
    mock_meeting = Meeting(
        id=uuid.uuid4(),
        project_id=project_id,
        meeting_name="Test Meeting",
        original_filename="test.mp4"
    )
    
    with patch('src.services.database_service.Meeting', return_value=mock_meeting):
        result = await db_service.create_meeting(
            project_id=project_id,
            meeting_name="Test Meeting",
            original_filename="test.mp4",
            file_path="path/to/test.mp4",
            file_size=1000,
            content_type="video/mp4"
        )
        
        assert result == mock_meeting
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_meeting(db_service, mock_session):
    """Test getting a meeting by ID."""
    meeting_id = uuid.uuid4()
    mock_meeting = Meeting(id=meeting_id, meeting_name="Test Meeting")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_meeting
    mock_session.execute.return_value = mock_result
    
    result = await db_service.get_meeting(meeting_id)
    
    assert result == mock_meeting
    mock_session.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_meeting_not_found(db_service, mock_session):
    """Test getting a non-existent meeting."""
    meeting_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    result = await db_service.get_meeting(meeting_id)
    
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_meetings_by_project(db_service, mock_session):
    """Test getting meetings by project."""
    project_id = uuid.uuid4()
    mock_meetings = [
        Meeting(id=uuid.uuid4(), project_id=project_id, meeting_name="Meeting 1"),
        Meeting(id=uuid.uuid4(), project_id=project_id, meeting_name="Meeting 2"),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_meetings
    mock_session.execute.return_value = mock_result
    
    result = await db_service.get_meetings_by_project(project_id, skip=0, limit=10)
    
    assert len(result) == 2
    assert result == mock_meetings


@pytest.mark.unit
@pytest.mark.asyncio
async def test_count_meetings_by_project(db_service, mock_session):
    """Test counting meetings by project."""
    project_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 3
    mock_session.execute.return_value = mock_result
    
    result = await db_service.count_meetings_by_project(project_id)
    
    assert result == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_meeting_status(db_service, mock_session):
    """Test updating meeting status."""
    meeting_id = uuid.uuid4()
    mock_meeting = Meeting(id=meeting_id, status="processing")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_meeting
    mock_session.execute.return_value = mock_result
    mock_session.commit = AsyncMock()
    
    result = await db_service.update_meeting_status(meeting_id, "completed")
    
    assert result == mock_meeting
    assert mock_meeting.status == "completed"
    assert mock_meeting.processing_completed_at is not None
    mock_session.flush.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_meeting_status_not_found(db_service, mock_session):
    """Test updating status for non-existent meeting."""
    meeting_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    result = await db_service.update_meeting_status(meeting_id, "completed")
    
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_meeting_paths(db_service, mock_session):
    """Test updating meeting paths."""
    meeting_id = uuid.uuid4()
    mock_meeting = Meeting(id=meeting_id)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_meeting
    mock_session.execute.return_value = mock_result
    
    result = await db_service.update_meeting_paths(
        meeting_id, transcript_path="transcript.json", diarized_transcript_path="diarized.json"
    )
    
    assert result == mock_meeting
    assert mock_meeting.transcript_path == "transcript.json"
    assert mock_meeting.diarized_transcript_path == "diarized.json"
    mock_session.flush.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_meeting(db_service, mock_session):
    """Test deleting a meeting."""
    meeting_id = uuid.uuid4()
    mock_meeting = Meeting(id=meeting_id)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_meeting
    mock_session.execute.return_value = mock_result
    
    result = await db_service.delete_meeting(meeting_id)
    
    assert result is True
    mock_session.delete.assert_called_once_with(mock_meeting)
    mock_session.flush.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_all_meetings(db_service, mock_session):
    """Test listing all meetings."""
    mock_meetings = [
        Meeting(id=uuid.uuid4(), meeting_name="Meeting 1"),
        Meeting(id=uuid.uuid4(), meeting_name="Meeting 2"),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_meetings
    mock_session.execute.return_value = mock_result
    
    result = await db_service.list_all_meetings(skip=0, limit=10)
    
    assert len(result) == 2
    assert result == mock_meetings


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_transcript(db_service, mock_session):
    """Test saving a transcript."""
    meeting_id = uuid.uuid4()
    from src.models.db_models import Transcript
    
    with patch('src.services.database_service.Transcript') as mock_transcript_class:
        mock_transcript = Transcript(meeting_id=meeting_id, text="Test transcript")
        mock_transcript_class.return_value = mock_transcript
        
        result = await db_service.save_transcript(meeting_id, "Test transcript", "whisper")
        
        assert result == mock_transcript
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_transcript(db_service, mock_session):
    """Test getting a transcript."""
    meeting_id = uuid.uuid4()
    from src.models.db_models import Transcript
    mock_transcript = Transcript(meeting_id=meeting_id, text="Test transcript")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_transcript
    mock_session.execute.return_value = mock_result
    
    result = await db_service.get_transcript(meeting_id)
    
    assert result == mock_transcript


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_topics(db_service, mock_session):
    """Test saving topics."""
    meeting_id = uuid.uuid4()
    topics_data = [
        {"topic": "Topic 1", "summary": "Summary 1", "start": 0.0, "end": 10.0},
        {"topic": "Topic 2", "summary": "Summary 2", "start": 10.0, "end": 20.0},
    ]
    
    with patch('src.services.database_service.Topic') as mock_topic_class:
        mock_topics = []
        for data in topics_data:
            mock_topic = MagicMock()
            mock_topic_class.return_value = mock_topic
            mock_topics.append(mock_topic)
        
        result = await db_service.save_topics(meeting_id, topics_data)
        
        assert len(result) == 2
        assert mock_session.add.call_count == 2
        mock_session.flush.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_topics(db_service, mock_session):
    """Test getting topics."""
    meeting_id = uuid.uuid4()
    from src.models.db_models import Topic
    mock_topics = [
        Topic(id=uuid.uuid4(), meeting_id=meeting_id, topic="Topic 1"),
        Topic(id=uuid.uuid4(), meeting_id=meeting_id, topic="Topic 2"),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_topics
    mock_session.execute.return_value = mock_result
    
    result = await db_service.get_topics(meeting_id)
    
    assert len(result) == 2
    assert result == mock_topics


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_topics(db_service, mock_session):
    """Test deleting topics."""
    meeting_id = uuid.uuid4()
    from src.models.db_models import Topic
    mock_topics = [Topic(id=uuid.uuid4(), meeting_id=meeting_id)]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_topics
    mock_session.execute.return_value = mock_result
    
    result = await db_service.delete_topics(meeting_id)
    
    assert result is True
    # delete is called for each topic (it's awaited in the loop)
    assert mock_session.delete.call_count == 1
    mock_session.flush.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_decisions(db_service, mock_session):
    """Test saving decisions."""
    meeting_id = uuid.uuid4()
    decisions_data = [
        {"decision": "Decision 1", "timestamp": 5.0},
        {"decision": "Decision 2", "timestamp": 10.0},
    ]
    
    with patch('src.services.database_service.Decision') as mock_decision_class:
        mock_decisions = []
        for data in decisions_data:
            mock_decision = MagicMock()
            mock_decision_class.return_value = mock_decision
            mock_decisions.append(mock_decision)
        
        result = await db_service.save_decisions(meeting_id, decisions_data)
        
        assert len(result) == 2
        assert mock_session.add.call_count == 2
        mock_session.flush.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_action_items(db_service, mock_session):
    """Test saving action items."""
    meeting_id = uuid.uuid4()
    action_items_data = [
        {"action": "Task 1", "assignee": "Alice", "due": "Friday"},
        {"action": "Task 2", "assignee": "Bob", "due": "Monday"},
    ]
    
    with patch('src.services.database_service.ActionItem') as mock_action_class:
        mock_actions = []
        for data in action_items_data:
            mock_action = MagicMock()
            mock_action_class.return_value = mock_action
            mock_actions.append(mock_action)
        
        result = await db_service.save_action_items(meeting_id, action_items_data)
        
        assert len(result) == 2
        assert mock_session.add.call_count == 2
        mock_session.flush.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_summary(db_service, mock_session):
    """Test saving a summary."""
    meeting_id = uuid.uuid4()
    from src.models.db_models import Summary
    
    with patch('src.services.database_service.Summary') as mock_summary_class:
        mock_summary = Summary(meeting_id=meeting_id, summary_text="Test summary")
        mock_summary_class.return_value = mock_summary
        
        result = await db_service.save_summary(meeting_id, "Test summary")
        
        assert result == mock_summary
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_summary(db_service, mock_session):
    """Test getting a summary."""
    meeting_id = uuid.uuid4()
    from src.models.db_models import Summary
    mock_summary = Summary(meeting_id=meeting_id, summary_text="Test summary")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_summary
    mock_session.execute.return_value = mock_result
    
    result = await db_service.get_summary(meeting_id)
    
    assert result == mock_summary


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_sentiment_analysis(db_service, mock_session):
    """Test saving sentiment analysis."""
    meeting_id = uuid.uuid4()
    
    with patch('src.services.database_service.SentimentAnalysis') as mock_sentiment_class:
        mock_sentiment = SentimentAnalysis(id=uuid.uuid4(), meeting_id=meeting_id)
        mock_sentiment_class.return_value = mock_sentiment
        
        result = await db_service.save_sentiment_analysis(meeting_id, "positive", 0.8)
        
        assert result == mock_sentiment
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_sentiment_analysis(db_service, mock_session):
    """Test getting sentiment analysis."""
    meeting_id = uuid.uuid4()
    mock_sentiment = SentimentAnalysis(id=uuid.uuid4(), meeting_id=meeting_id, overall_sentiment="positive")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_sentiment
    mock_session.execute.return_value = mock_result
    
    result = await db_service.get_sentiment_analysis(meeting_id)
    
    assert result == mock_sentiment


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_action_item_status(db_service, mock_session):
    """Test updating action item status."""
    action_item_id = uuid.uuid4()
    mock_action = ActionItem(id=action_item_id, status="pending")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_action
    mock_session.execute.return_value = mock_result
    
    result = await db_service.update_action_item_status(action_item_id, "completed")
    
    assert result == mock_action
    assert mock_action.status == "completed"
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_action_item_status_not_found(db_service, mock_session):
    """Test updating status for non-existent action item."""
    action_item_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    result = await db_service.update_action_item_status(action_item_id, "completed")
    
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_summary(db_service, mock_session):
    """Test deleting a summary."""
    meeting_id = uuid.uuid4()
    mock_summary = Summary(id=uuid.uuid4(), meeting_id=meeting_id)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_summary
    mock_session.execute.return_value = mock_result
    
    result = await db_service.delete_summary(meeting_id)
    
    assert result is True
    mock_session.delete.assert_called_once_with(mock_summary)
    mock_session.flush.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_summary_not_found(db_service, mock_session):
    """Test deleting a non-existent summary."""
    meeting_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    result = await db_service.delete_summary(meeting_id)
    
    assert result is False
    mock_session.delete.assert_not_called()

