"""Prometheus metrics for monitoring.

This module provides metrics collection that gracefully handles cases where
prometheus_client is not available, ensuring the application continues to work.
"""

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import prometheus_client, but don't fail if it's not available
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning(
        "prometheus_client not available. Metrics collection will be disabled. "
        "Install with: pip install prometheus-client"
    )
    
    # Create dummy classes that do nothing
    class Counter:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def inc(self, value=1):
            pass
    
    class Histogram:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def observe(self, value):
            pass
        def time(self):
            return self
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    
    class Gauge:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, **kwargs):
            return self
        def set(self, value):
            pass
        def inc(self, value=1):
            pass
        def dec(self, value=1):
            pass
    
    def generate_latest():
        return b"# Prometheus metrics not available\n"
    
    CONTENT_TYPE_LATEST = "text/plain"


# HTTP Request Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)

# Meeting Processing Metrics
meeting_processing_total = Counter(
    'meeting_processing_total',
    'Total number of meetings processed',
    ['status']  # success, error, timeout
)

meeting_processing_duration_seconds = Histogram(
    'meeting_processing_duration_seconds',
    'Meeting processing duration in seconds',
    ['stage'],  # transcription, agents, total
    buckets=(10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0)
)

# Agent Execution Metrics
agent_executions_total = Counter(
    'agent_executions_total',
    'Total number of agent executions',
    ['agent_name', 'status']  # topic_agent, decision_agent, etc. | success, error
)

agent_execution_duration_seconds = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_name'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0)
)

# Vector Store Metrics
vector_store_size = Gauge(
    'vector_store_size',
    'Number of vectors in the vector store'
)

vector_search_requests_total = Counter(
    'vector_search_requests_total',
    'Total number of vector search requests',
    ['status']  # success, error
)

vector_search_duration_seconds = Histogram(
    'vector_search_duration_seconds',
    'Vector search duration in seconds',
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0)
)

# Database Metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total number of database queries',
    ['operation', 'status']  # select, insert, update, delete | success, error
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0)
)


def get_metrics_content() -> bytes:
    """Get Prometheus metrics in text format."""
    if not PROMETHEUS_AVAILABLE:
        return b"# Prometheus metrics not available\n# Install prometheus-client to enable metrics\n"
    return generate_latest()


def get_metrics_content_type() -> str:
    """Get the content type for metrics endpoint."""
    return CONTENT_TYPE_LATEST if PROMETHEUS_AVAILABLE else "text/plain"


class MetricsTimer:
    """Context manager for timing operations."""
    
    def __init__(self, histogram: Histogram, labels: Optional[dict] = None):
        self.histogram = histogram
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            if self.labels:
                self.histogram.labels(**self.labels).observe(duration)
            else:
                self.histogram.observe(duration)

