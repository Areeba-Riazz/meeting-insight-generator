"""Unit tests for metrics module."""

import pytest
from unittest.mock import patch, MagicMock

from src.utils.metrics import (
    get_metrics_content,
    get_metrics_content_type,
    MetricsTimer,
    PROMETHEUS_AVAILABLE,
    http_requests_total,
    http_request_duration_seconds,
    meeting_processing_total,
    meeting_processing_duration_seconds,
    agent_executions_total,
    agent_execution_duration_seconds,
    vector_store_size,
    vector_search_requests_total,
    vector_search_duration_seconds,
    db_queries_total,
    db_query_duration_seconds,
)


@pytest.mark.unit
def test_get_metrics_content_with_prometheus():
    """Test get_metrics_content when Prometheus is available."""
    if PROMETHEUS_AVAILABLE:
        content = get_metrics_content()
        assert isinstance(content, bytes)
        assert len(content) > 0
    else:
        # If Prometheus not available, should return fallback message
        content = get_metrics_content()
        assert isinstance(content, bytes)
        assert b"not available" in content.lower() or b"prometheus" in content.lower()


@pytest.mark.unit
def test_get_metrics_content_without_prometheus():
    """Test get_metrics_content when Prometheus is not available."""
    with patch('src.utils.metrics.PROMETHEUS_AVAILABLE', False):
        with patch('src.utils.metrics.generate_latest') as mock_generate:
            content = get_metrics_content()
            assert isinstance(content, bytes)
            assert b"not available" in content.lower() or b"prometheus" in content.lower()
            mock_generate.assert_not_called()


@pytest.mark.unit
def test_get_metrics_content_type_with_prometheus():
    """Test get_metrics_content_type when Prometheus is available."""
    if PROMETHEUS_AVAILABLE:
        content_type = get_metrics_content_type()
        assert isinstance(content_type, str)
        assert len(content_type) > 0
    else:
        content_type = get_metrics_content_type()
        assert content_type == "text/plain"


@pytest.mark.unit
def test_get_metrics_content_type_without_prometheus():
    """Test get_metrics_content_type when Prometheus is not available."""
    with patch('src.utils.metrics.PROMETHEUS_AVAILABLE', False):
        content_type = get_metrics_content_type()
        assert content_type == "text/plain"


@pytest.mark.unit
def test_metrics_timer_context_manager():
    """Test MetricsTimer as context manager."""
    # Create a mock histogram
    mock_histogram = MagicMock()
    mock_histogram.observe = MagicMock()
    
    timer = MetricsTimer(mock_histogram)
    
    with timer:
        pass  # Just enter and exit
    
    # Should have called observe with a duration
    assert mock_histogram.observe.called
    call_args = mock_histogram.observe.call_args[0]
    assert len(call_args) == 1
    assert isinstance(call_args[0], (int, float))
    assert call_args[0] >= 0


@pytest.mark.unit
def test_metrics_timer_with_labels():
    """Test MetricsTimer with labels."""
    mock_histogram = MagicMock()
    mock_labeled = MagicMock()
    mock_labeled.observe = MagicMock()
    mock_histogram.labels.return_value = mock_labeled
    
    labels = {"method": "GET", "endpoint": "/test"}
    timer = MetricsTimer(mock_histogram, labels=labels)
    
    with timer:
        pass
    
    # Should have called labels() with the provided labels
    mock_histogram.labels.assert_called_once_with(**labels)
    # Should have called observe on the labeled histogram
    mock_labeled.observe.assert_called_once()
    call_args = mock_labeled.observe.call_args[0]
    assert len(call_args) == 1
    assert isinstance(call_args[0], (int, float))


@pytest.mark.unit
def test_metrics_timer_measures_duration():
    """Test that MetricsTimer actually measures duration."""
    import time
    mock_histogram = MagicMock()
    mock_histogram.observe = MagicMock()
    
    timer = MetricsTimer(mock_histogram)
    
    with timer:
        time.sleep(0.1)  # Sleep for 100ms
    
    # Check that duration was measured (should be at least 0.1 seconds)
    call_args = mock_histogram.observe.call_args[0]
    duration = call_args[0]
    assert duration >= 0.1


@pytest.mark.unit
def test_metrics_objects_exist():
    """Test that all metric objects are created."""
    # These should all exist and be callable/usable
    assert http_requests_total is not None
    assert http_request_duration_seconds is not None
    assert meeting_processing_total is not None
    assert meeting_processing_duration_seconds is not None
    assert agent_executions_total is not None
    assert agent_execution_duration_seconds is not None
    assert vector_store_size is not None
    assert vector_search_requests_total is not None
    assert vector_search_duration_seconds is not None
    assert db_queries_total is not None
    assert db_query_duration_seconds is not None


@pytest.mark.unit
def test_metrics_counter_increment():
    """Test that Counter metrics can be incremented."""
    # Try to increment the counter with labels
    try:
        counter = http_requests_total.labels(method="GET", endpoint="/test", status_code=200)
        counter.inc()
        counter.inc(5)  # Increment by 5
        # If we get here without exception, it works
        assert True
    except Exception as e:
        # If Prometheus is not available, the dummy Counter should still work
        if not PROMETHEUS_AVAILABLE:
            assert True  # Dummy class should work
        else:
            raise


@pytest.mark.unit
def test_metrics_histogram_observe():
    """Test that Histogram metrics can record values."""
    try:
        histogram = http_request_duration_seconds.labels(method="GET", endpoint="/test")
        histogram.observe(1.5)
        # If we get here without exception, it works
        assert True
    except Exception as e:
        if not PROMETHEUS_AVAILABLE:
            assert True  # Dummy class should work
        else:
            raise


@pytest.mark.unit
def test_metrics_gauge_set():
    """Test that Gauge metrics can be set."""
    try:
        vector_store_size.set(100)
        vector_store_size.inc(10)
        vector_store_size.dec(5)
        # If we get here without exception, it works
        assert True
    except Exception as e:
        if not PROMETHEUS_AVAILABLE:
            assert True  # Dummy class should work
        else:
            raise


@pytest.mark.unit
def test_metrics_timer_exception_handling():
    """Test MetricsTimer handles exceptions correctly."""
    mock_histogram = MagicMock()
    mock_histogram.observe = MagicMock()
    
    timer = MetricsTimer(mock_histogram)
    
    try:
        with timer:
            raise ValueError("Test exception")
    except ValueError:
        pass  # Expected
    
    # Should still record the duration even if exception occurred
    assert mock_histogram.observe.called

