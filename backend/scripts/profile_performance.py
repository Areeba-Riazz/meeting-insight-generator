"""Script to profile performance bottlenecks."""

import cProfile
import pstats
import io
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.agent_orchestrator import AgentOrchestrator
from src.services.transcription_service import TranscriptionService, TranscriptionResult, TranscriptionSegment
from src.agents.topic_agent import TopicAgent
from src.agents.decision_agent import DecisionAgent
from src.agents.action_item_agent import ActionItemAgent
from src.agents.sentiment_agent import SentimentAgent
from src.agents.summary_agent import SummaryAgent


def create_test_data():
    """Create test data for profiling."""
    text = " ".join([f"Sentence {i} with some content for testing." for i in range(500)])
    segments = [
        TranscriptionSegment(
            text=f"Sentence {i} with some content for testing.",
            start=i * 2.0,
            end=(i + 1) * 2.0,
            speaker=f"SPEAKER_{i % 3}"
        )
        for i in range(500)
    ]
    return TranscriptionResult(text=text, segments=segments, model="test")


async def profile_agent_execution():
    """Profile agent execution."""
    # Create test data
    transcript = create_test_data()
    
    # Mock transcription service
    class MockTranscriptionService:
        def transcribe(self, audio_path, meeting_id=None, on_status=None):
            return transcript
    
    # Create agents
    agents = [
        TopicAgent(),
        DecisionAgent(),
        ActionItemAgent(),
        SentimentAgent(),
        SummaryAgent(),
    ]
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        transcription_service=MockTranscriptionService(),
        agents=agents
    )
    
    # Profile
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run pipeline
    import asyncio
    from unittest.mock import MagicMock
    audio_path = Path("test_audio.wav")
    audio_path.touch()
    
    try:
        await orchestrator.process(
            meeting_id="profile_test",
            audio_path=audio_path,
            on_status=lambda *args: None
        )
    except Exception as e:
        print(f"Error during profiling: {e}")
    
    profiler.disable()
    
    # Generate report
    s = io.StringIO()
    stats = pstats.Stats(profiler, stream=s)
    stats.sort_stats('cumulative')
    stats.print_stats(30)  # Top 30 functions
    
    print("=" * 80)
    print("Performance Profile - Top 30 Functions by Cumulative Time")
    print("=" * 80)
    print(s.getvalue())
    
    # Save to file
    output_file = Path("performance_profile.txt")
    with open(output_file, "w") as f:
        f.write(s.getvalue())
    print(f"\n📊 Full profile saved to: {output_file}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(profile_agent_execution())

