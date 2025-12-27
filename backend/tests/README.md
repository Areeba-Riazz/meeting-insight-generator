# Testing Guide

This directory contains the test suite for the Meeting Insight Generator backend.

## Test Structure

```
tests/
├── unit/              # Fast, isolated unit tests
│   └── test_agents/   # Agent unit tests
├── integration/       # Component integration tests
│   └── test_api/      # API endpoint tests
├── e2e/               # End-to-end pipeline tests
├── performance/       # Performance and load tests
└── conftest.py        # Shared fixtures
```

## Running Tests

### Run All Tests
```bash
cd backend
pytest
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html
```

### Run Specific Test Types
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# End-to-end tests only
pytest -m e2e

# Performance tests only
pytest -m performance
```

### Run Specific Test File
```bash
pytest tests/unit/test_agents/test_topic_agent.py
```

### Run with Verbose Output
```bash
pytest -v
```

## Test Scripts

### Run Tests with Coverage Report
```bash
python scripts/run_tests.py
```

### Profile Performance
```bash
python scripts/profile_performance.py
```

## Coverage Goals

- **Target**: >80% code coverage
- **Current**: Check with `pytest --cov=src --cov-report=term-missing`

## Test Markers

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (require services)
- `@pytest.mark.e2e` - End-to-end tests (full pipeline)
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.requires_gpu` - Tests requiring GPU

## Writing Tests

### Unit Test Example
```python
import pytest
from src.agents.topic_agent import TopicAgent

@pytest.mark.unit
@pytest.mark.asyncio
async def test_topic_agent_basic():
    agent = TopicAgent()
    result = await agent.run({"text": "Test transcript", "segments": []})
    assert "topics" in result
```

### Integration Test Example
```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.mark.integration
def test_upload_endpoint(client):
    response = client.post("/api/v1/upload", files={"file": ...})
    assert response.status_code == 200
```

## Fixtures

Common fixtures are available in `conftest.py`:
- `client` - FastAPI test client
- `async_client` - Async test client
- `temp_storage_dir` - Temporary storage directory
- `sample_transcript_data` - Sample transcript for testing
- `mock_env_vars` - Mocked environment variables

## Continuous Integration

Tests are configured to run in CI/CD pipelines with:
- Coverage reporting
- XML output for CI tools
- HTML reports for local viewing

