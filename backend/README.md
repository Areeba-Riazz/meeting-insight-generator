# Backend - Meeting Insight Generator

FastAPI backend for the Meeting Insight Generator project. Processes meeting audio/video files through transcription and multi-agent AI analysis to extract structured insights.

## Tech Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy** - Async ORM with PostgreSQL
- **WhisperX** - Speech recognition with speaker diarization
- **pyannote.audio** - Speaker diarization pipeline
- **FAISS** - Vector similarity search
- **sentence-transformers** - Embedding generation
- **Mistral AI / Groq** - LLM providers
- **HuggingFace Transformers** - Sentiment analysis
- **Prometheus Client** - Metrics collection

## Architecture

### Core Components

- **API Routes** (`src/api/routes/`) - REST endpoints for upload, status, insights, search, projects, chat
- **AI Agents** (`src/agents/`) - Five specialized agents:
  - Topic Agent - Topic segmentation
  - Decision Agent - Decision extraction
  - Action Item Agent - Task extraction
  - Sentiment Agent - Sentiment analysis
  - Summary Agent - Executive summaries
- **Services** (`src/services/`) - Business logic:
  - Agent Orchestrator - Pipeline management
  - Transcription Service - WhisperX integration
  - Vector Store Service - FAISS-based semantic search
  - Database Service - CRUD operations
- **Models** (`src/models/`) - SQLAlchemy database models
- **Core** (`src/core/`) - Database configuration and connection management

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL (optional, filesystem fallback available)
- FFmpeg (for video processing)

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Configuration

Create `.env` file:
```env
# Database (optional)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/meeting_insights

# LLM Configuration
MISTRAL_API_KEY=your_mistral_api_key
GROQ_API_KEY=your_groq_api_key
MODEL_TYPE=mistral

# Whisper Configuration
WHISPER_MODEL=small
WHISPER_DEVICE=cpu
HUGGINGFACE_TOKEN=your_huggingface_token

# Vector Store
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_PATH=./storage/vectors

# API Configuration
API_HOST=0.0.0.0
API_PORT=3000
```

### Database Setup (Optional)

```bash
python scripts/setup_db.py
```

### Running

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 3000

# Production
python main.py
```

## API Endpoints

### Core Endpoints
- `POST /api/v1/upload` - Upload meeting file
- `GET /api/v1/status/{meeting_id}` - Get processing status
- `GET /api/v1/insights/{meeting_id}` - Retrieve insights
- `POST /api/v1/search` - Semantic search
- `POST /api/v1/chat` - AI chatbot with RAG

### Project Management
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Monitoring
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

### Documentation
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc

## Processing Pipeline

1. **Upload** - File validation and storage
2. **Transcription** - WhisperX with speaker diarization
3. **Agent Processing** - Sequential execution of 5 AI agents
4. **Storage** - Save to database, file system, and vector store
5. **Completion** - Results available via API

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test types
pytest -m unit
pytest -m integration
pytest -m e2e
```

## Project Structure

```
backend/
├── src/
│   ├── api/          # API routes and models
│   ├── agents/       # AI agents
│   ├── core/         # Database configuration
│   ├── models/       # Database models
│   ├── services/     # Business logic
│   └── utils/        # Utilities
├── tests/            # Test suite
├── scripts/          # Setup scripts
├── storage/          # File storage
└── main.py           # Application entry point
```
