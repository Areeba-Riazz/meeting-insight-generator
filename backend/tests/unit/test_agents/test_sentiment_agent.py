"""Unit tests for SentimentAgent."""

import pytest
from unittest.mock import MagicMock, patch

from src.agents.sentiment_agent import SentimentAgent


@pytest.fixture
def sentiment_agent():
    """Create a SentimentAgent instance for testing."""
    return SentimentAgent()


@pytest.fixture
def sample_transcript():
    """Sample transcript data for testing."""
    return {
        "text": "This is a great meeting! We made excellent progress. Everyone is happy with the results.",
        "segments": [
            {"text": "This is a great meeting!", "start": 0.0, "end": 3.0},
            {"text": "We made excellent progress.", "start": 3.0, "end": 6.0},
            {"text": "Everyone is happy with the results.", "start": 6.0, "end": 9.0},
        ],
        "meeting_id": "test_meeting_001"
    }


@pytest.mark.asyncio
async def test_sentiment_agent_run_success(sentiment_agent, sample_transcript):
    """Test successful sentiment analysis."""
    result = await sentiment_agent.run(sample_transcript)
    
    assert "sentiment" in result
    sentiment_data = result["sentiment"]
    assert "overall" in sentiment_data
    assert "score" in sentiment_data
    assert "segments" in sentiment_data
    assert sentiment_data["overall"] in ["Positive", "Negative", "Neutral"]


@pytest.mark.asyncio
async def test_sentiment_agent_run_empty_input(sentiment_agent):
    """Test with empty input."""
    payload = {"text": "", "segments": []}
    
    result = await sentiment_agent.run(payload)
    
    assert "sentiment" in result
    assert "overall" in result["sentiment"]


@pytest.mark.asyncio
async def test_sentiment_agent_positive_sentiment(sentiment_agent):
    """Test detection of positive sentiment."""
    payload = {
        "text": "Great work! Excellent progress. We're very happy with the results.",
        "segments": [
            {"text": "Great work! Excellent progress.", "start": 0.0, "end": 3.0},
        ]
    }
    
    result = await sentiment_agent.run(payload)
    
    # Should detect positive sentiment
    assert result["sentiment"]["overall"] in ["Positive", "Neutral"]


@pytest.mark.asyncio
async def test_sentiment_agent_negative_sentiment(sentiment_agent):
    """Test detection of negative sentiment."""
    payload = {
        "text": "This is a problem. We're concerned about the delays. This is not good.",
        "segments": [
            {"text": "This is a problem. We're concerned about the delays.", "start": 0.0, "end": 3.0},
        ]
    }
    
    result = await sentiment_agent.run(payload)
    
    # Should detect negative or neutral sentiment
    assert result["sentiment"]["overall"] in ["Negative", "Neutral"]


def test_calculate_weighted_sentiment(sentiment_agent):
    """Test weighted sentiment calculation."""
    positive_words = ["great", "excellent", "good"]
    score = sentiment_agent._calculate_weighted_sentiment(positive_words)
    
    assert score > 0  # Should be positive


def test_handle_negations(sentiment_agent):
    """Test negation handling."""
    words = ["not", "good", "but", "excellent"]
    words_result, is_negated = sentiment_agent._handle_negations(words)
    
    assert len(is_negated) == len(words)
    # "good" should be negated
    assert is_negated[1] is True


def test_extract_ngrams(sentiment_agent):
    """Test n-gram extraction."""
    words = ["this", "is", "a", "test"]
    bigrams = sentiment_agent._extract_ngrams(words, n=2)
    
    assert len(bigrams) == 3
    assert "this is" in bigrams
    assert "is a" in bigrams
    assert "a test" in bigrams


def test_analyze_punctuation(sentiment_agent):
    """Test punctuation analysis."""
    text1 = "Great!!!"
    score1 = sentiment_agent._analyze_punctuation(text1)
    assert score1 > 0  # Exclamations should add positive weight
    
    text2 = "What??? Really???"
    score2 = sentiment_agent._analyze_punctuation(text2)
    assert score2 < 0  # Questions should add negative weight


def test_handle_contrast(sentiment_agent):
    """Test contrast handling."""
    text = "This is bad, but that is good"
    contrast_score = sentiment_agent._handle_contrast(text)
    
    assert contrast_score is not None
    # Second part should have more weight


def test_analyze_by_sentences(sentiment_agent):
    """Test sentence-by-sentence analysis."""
    text = "This is great! We're very happy. Excellent work!"
    result = sentiment_agent._analyze_by_sentences(text)
    
    assert "sentiment" in result
    assert "score" in result
    assert "consistency" in result
    assert result["sentiment"] in ["Positive", "Negative", "Neutral"]


def test_huggingface_client_query_success(sentiment_agent):
    """Test HuggingFace client query."""
    mock_response = [
        [
            {"label": "POSITIVE", "score": 0.9},
            {"label": "NEGATIVE", "score": 0.05},
            {"label": "NEUTRAL", "score": 0.05}
        ]
    ]
    
    with patch('src.agents.sentiment_agent.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response
        
        result = sentiment_agent._analyze_sentiment_hf("Great meeting!")
        
        assert result is not None
        assert result["sentiment"] == "POSITIVE"
        assert result["score"] == 0.9

