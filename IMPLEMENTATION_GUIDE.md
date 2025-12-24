# Meeting Insight Generator - Complete Implementation Guide

## Table of Contents
1. [Technology Stack](#technology-stack)
2. [Repository Structure](#repository-structure)
3. [System Architecture](#system-architecture)
4. [Implementation Phases](#implementation-phases)
5. [Frontend Plan (React)](#frontend-plan-react)
6. [Setup Instructions](#setup-instructions)
7. [Development Workflow](#development-workflow)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Guide](#deployment-guide)



---

## Technology Stack

### Core Framework & Libraries

#### 1. **Agent Framework: LangChain**
- **Version**: `langchain>=0.1.0,<0.3.0`
- **Purpose**: Orchestrates multi-agent workflows, manages LLM interactions
- **Key Components**:
  - `langchain.agents`: Agent creation and execution
  - `langchain.chains`: Chain-based processing
  - `langchain.tools`: Tool definitions for agents
  - `langchain.prompts`: Prompt templates
  - `langchain.memory`: Conversation memory management

#### 2. **Language Models**
- **Primary**: **Mistral AI** (via `mistralai` SDK or HuggingFace)
  - Model: `mistralai/Mistral-7B-Instruct-v0.2` or API
  - Use case: Analysis tasks (topic segmentation, decision extraction, sentiment)
- **Alternative**: **LLaMA 3.1** (via `llama-cpp-python` or HuggingFace)
  - Model: `meta-llama/Meta-Llama-3.1-8B-Instruct`
  - Use case: Fallback or cost-effective option
- **Libraries**:
  - `transformers>=4.35.0`: HuggingFace transformers
  - `torch>=2.0.0`: PyTorch for local model inference
  - `mistralai>=0.1.0`: Official Mistral SDK (if using API)

#### 3. **Speech Recognition: Whisper**
- **Library**: `openai-whisper>=20231117`
- **Model**: `whisper-large-v3` (or `whisper-medium` for faster processing)
- **Features**: 
  - Multi-language support
  - Speaker diarization (via `pyannote.audio` or similar)
  - Timestamp generation
- **Alternative**: `faster-whisper` for optimized performance

#### 4. **Vector Database: FAISS**
- **Library**: `faiss-cpu>=1.7.4` (or `faiss-gpu` for GPU acceleration)
- **Purpose**: Store and search meeting embeddings for RAG
- **Integration**: `langchain.vectorstores.FAISS`
- **Embeddings**: `sentence-transformers` (all-MiniLM-L6-v2 or all-mpnet-base-v2)

#### 5. **Backend Framework: FastAPI**
- **Version**: `fastapi>=0.104.0`
- **Features**: 
  - Async request handling
  - Automatic API documentation (Swagger/OpenAPI)
  - Request validation
- **Additional**:
  - `uvicorn[standard]>=0.24.0`: ASGI server
  - `python-multipart>=0.0.6`: File upload handling
  - `pydantic>=2.0.0`: Data validation

#### 6. **Database: PostgreSQL**
- **Version**: PostgreSQL 15+ (via Docker)
- **ORM**: `sqlalchemy>=2.0.0`
- **Migrations**: `alembic>=1.12.0`
- **Connection**: `asyncpg>=0.29.0` (async PostgreSQL driver)
- **Additional**: `psycopg2-binary>=2.9.9` (fallback)

#### 7. **Containerization: Docker**
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.20+
- **Multi-stage builds** for optimization

### Supporting Libraries

#### Audio Processing
- `pydub>=0.25.1`: Audio manipulation
- `librosa>=0.10.0`: Audio analysis
- `soundfile>=0.12.0`: Audio file I/O

#### Data Processing
- `numpy>=1.24.0`: Numerical operations
- `pandas>=2.0.0`: Data manipulation
- `python-dateutil>=2.8.2`: Date parsing

#### Utilities
- `python-dotenv>=1.0.0`: Environment variables
- `httpx>=0.25.0`: HTTP client (for async API calls)
- `aiofiles>=23.2.0`: Async file operations
- `tenacity>=8.2.0`: Retry logic
- `loguru>=0.7.0`: Logging

#### Testing
- `pytest>=7.4.0`: Testing framework
- `pytest-asyncio>=0.21.0`: Async test support
- `pytest-cov>=4.1.0`: Coverage reporting
- `httpx>=0.25.0`: Test client for FastAPI
- `faker>=19.0.0`: Test data generation

#### Development Tools
- `black>=23.11.0`: Code formatting
- `flake8>=6.1.0`: Linting
- `mypy>=1.7.0`: Type checking

---

## Repository Structure

```
nlp_project/
├── README.md                          # Project overview
├── IMPLEMENTATION_GUIDE.md            # This file
├── .gitignore                         # Git ignore rules
│
├── backend/                           # Backend application
│   ├── src/                           # Main source code
│   ├── tests/                         # Test suite
│   ├── scripts/                       # Utility scripts
│   ├── migrations/                    # Database migrations
│   ├── storage/                       # Local storage
│   ├── Dockerfile                     # Backend Dockerfile
│   ├── docker-compose.yml             # Docker Compose configuration
│   ├── pytest.ini                     # Pytest configuration
│   └── pyproject.toml                 # Project metadata
├── requirements.txt                   # Python dependencies (shared venv at root)
│
├── frontend/                          # Frontend application
│   ├── README.md                      # Frontend documentation
│   ├── package.json                   # Frontend dependencies (planned)
│   ├── src/                           # React source (planned)
│   └── public/                        # Static assets (planned)
│
└── Documentation/                     # Project documentation
    └── Project_Proposal.pdf
│
├── src/                               # Main source code (now in backend/)
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry point
│   │
│   ├── api/                          # API layer
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── upload.py            # File upload endpoint
│   │   │   ├── status.py            # Processing status endpoint
│   │   │   ├── insights.py          # Insights retrieval endpoint
│   │   │   └── search.py            # Historical search endpoint
│   │   ├── models/                   # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── request.py           # Request models
│   │   │   └── response.py          # Response models
│   │   └── dependencies.py          # API dependencies (auth, DB sessions)
│   │
│   ├── core/                         # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py                # Application configuration
│   │   ├── database.py              # Database connection setup
│   │   └── logging.py                # Logging configuration
│   │
│   ├── services/                     # Business logic layer
│   │   ├── __init__.py
│   │   ├── transcription_service.py # Whisper transcription
│   │   ├── agent_orchestrator.py    # Multi-agent coordination
│   │   ├── vector_store_service.py  # FAISS vector operations
│   │   └── meeting_service.py       # Meeting CRUD operations
│   │
│   ├── agents/                       # AI agents
│   │   ├── __init__.py
│   │   ├── base_agent.py            # Base agent class
│   │   ├── topic_agent.py           # Topic segmentation agent
│   │   ├── decision_agent.py        # Decision extraction agent
│   │   ├── action_item_agent.py     # Action item extraction agent
│   │   ├── sentiment_agent.py       # Sentiment analysis agent
│   │   └── summary_agent.py         # Summary generation agent
│   │
│   ├── models/                       # Database models (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── meeting.py               # Meeting model
│   │   ├── transcript.py             # Transcript model
│   │   ├── insight.py               # Insight models (decisions, actions, etc.)
│   │   └── vector_embedding.py      # Vector embedding storage
│   │
│   ├── utils/                        # Utility functions
│   │   ├── __init__.py
│   │   ├── audio_utils.py           # Audio processing utilities
│   │   ├── text_utils.py            # Text processing utilities
│   │   └── validators.py            # Input validation
│   │
│   └── workers/                      # Background workers (optional)
│       ├── __init__.py
│       └── processing_worker.py    # Async processing worker
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/
│   │   ├── test_agents/
│   │   ├── test_services/
│   │   └── test_utils/
│   ├── integration/
│   │   ├── test_api/
│   │   └── test_pipeline/
│   └── fixtures/                    # Test data files
│       └── sample_audio/
│
├── scripts/                          # Utility scripts
│   ├── setup_db.py                  # Database initialization
│   ├── seed_data.py                 # Seed test data
│   └── migrate_vectors.py           # Vector store migration
│
├── migrations/                       # Alembic migrations
│   ├── versions/
│   └── env.py
│
├── docs/                             # Documentation
│   ├── api/                         # API documentation
│   ├── architecture/                # Architecture diagrams
│   └── deployment/                  # Deployment guides
│
└── storage/                          # Local storage (not in git)
    ├── {meeting_id}/                # Each meeting gets its own folder
    │   ├── audio/                   # Original audio/video file
    │   ├── transcript.txt           # Plain text transcript
    │   ├── transcript.json          # Structured transcript with timestamps
    │   ├── insights.json             # All insights (decisions, actions, topics, sentiment)
    │   ├── summary.txt              # Generated executive summary
    │   └── metadata.json             # Meeting metadata
    └── vectors/                      # Global FAISS index (shared across meetings)
```

---

## System Architecture

### High-Level Flow

```
┌─────────────┐
│ Audio Upload│
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ FastAPI Endpoint│
└──────┬──────────┘
       │
       ▼
┌─────────────────────┐
│ Transcription       │
│ (Whisper)           │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Agent Orchestrator  │
│ (LangChain)         │
└──────┬──────────────┘
       │
       ├──► Topic Agent ──────┐
       ├──► Decision Agent ───┤
       ├──► Action Item Agent─┤──► Structured Insights
       ├──► Sentiment Agent ──┤
       └──► Summary Agent ────┘
       │
       ▼
┌─────────────────────┐
│ Vector Store (FAISS)│
│ + PostgreSQL        │
└─────────────────────┘
```

### Component Details

#### 1. **API Layer (FastAPI)**
- **Endpoints**:
  - `POST /api/v1/upload`: Upload audio file
  - `GET /api/v1/status/{meeting_id}`: Check processing status
  - `GET /api/v1/insights/{meeting_id}`: Retrieve insights
  - `POST /api/v1/search`: Semantic search across meetings
- **Features**: Async processing, file validation, error handling

#### 2. **Transcription Service**
- Uses Whisper for audio-to-text conversion
- Handles multiple audio formats (mp3, wav, m4a, etc.)
- Adds speaker diarization (e.g., `pyannote.audio`) to label speakers and segment turns
- Extracts timestamps per segment and aligns diarization with transcript lines
- Stores raw transcript plus speaker/segment metadata in PostgreSQL

#### 3. **Agent Orchestrator**
- Coordinates multiple specialized agents
- Manages agent execution order and dependencies
- Handles error recovery and retries
- Aggregates agent outputs into structured format

#### 4. **Specialized Agents**
Each agent is a LangChain agent with specific tools and prompts:

- **Topic Agent**: Identifies conversation segments and topics
- **Decision Agent**: Extracts decisions with context and participants
- **Action Item Agent**: Identifies tasks, assignees, and deadlines
- **Sentiment Agent**: Analyzes emotional tone and engagement
- **Summary Agent**: Generates executive summary

#### 5. **Vector Store Service**
- Generates embeddings for meeting content
- Stores in FAISS for fast similarity search
- Links embeddings to PostgreSQL records
- Handles query processing for semantic search

#### 6. **Database Layer**
- **PostgreSQL Tables**:
  - `meetings`: Meeting metadata
  - `transcripts`: Full transcripts with timestamps
  - `topics`: Topic segments
  - `decisions`: Extracted decisions
  - `action_items`: Tasks and responsibilities
  - `sentiments`: Sentiment analysis results
  - `summaries`: Generated summaries

---

## Implementation Phases

### Phase 1: Foundation Setup (Week 1)

#### 1.1 Project Initialization
- [x] Set up repository structure
- [x] Create virtual environment
- [x] Install core dependencies
- [x] Configure Docker and Docker Compose
- [ ] Set up PostgreSQL database
- [x] Create environment configuration

#### 1.2 Persistence (Deferred until FAISS stage)
- [ ] Design database schema (later)
- [ ] Create SQLAlchemy models (later)
- [ ] Set up Alembic migrations (later)
- [ ] Create initial migration (later)
- [ ] Test database connections (later)

#### 1.3 Basic API Structure (pipeline-first, in-memory)
- [x] Initialize FastAPI application
- [x] Create basic route structure
- [x] Set up request/response models
- [x] Implement health check endpoint
- [x] Configure CORS and middleware
- [x] Use in-memory/temp storage for pipeline prototyping (persistence deferred to Phase 3 with FAISS/DB)

### Phase 2: Core Services (Week 2)

#### 2.1 Transcription Service
- [x] Integrate Whisper model (pipeline-first)
- [x] Implement audio preprocessing (normalize/resample via pydub)
- [x] Add speaker diarization hook (pyannote, optional token)
- [x] Create transcript storage logic (filesystem store; DB deferred)
- [x] Support and test video inputs (mp4/mkv/mov via ffmpeg audio extraction)
- [x] Test with sample audio files (script: backend/scripts/transcribe_sample.py)

#### 2.2 Agent Framework Setup
- [ ] Set up LangChain configuration (full prompts/tooling)
- [x] Create base agent class
- [x] Configure LLM connections (Mistral via LangChain with mock fallback)
- [x] Implement prompt templates (initial prompts added)
- [x] Create agent execution framework (orchestrator with timeouts/parallel)

#### 2.3 Individual Agents
- [x] Implement Topic Agent (LLM with prompt + fallback parsing)
- [x] Implement Decision Agent (LLM with prompt + fallback parsing)
- [x] Implement Action Item Agent (LLM with prompt + fallback parsing)
- [x] Implement Sentiment Agent (LLM with prompt)
- [x] Implement Summary Agent (LLM with prompt)
- [ ] Unit test each agent

#### 2.4 Orchestration & API (pipeline-first, in-memory)
- [x] Implement agent orchestrator (parallel with timeouts/errors)
- [x] Add upload endpoint (file upload to in-memory/FS pipeline; validation added)
- [x] Add status endpoint (in-memory state)
- [x] Add insights endpoint (in-memory results)
- [x] Add file-type/size validation; basic error handling
- [x] Support video via audio extraction (mp4/mkv/mov) — needs explicit validation tests

### Phase 3: Integration & Orchestration (Week 3)

#### 3.1 Agent Orchestrator
- [ ] Design orchestration workflow
- [ ] Implement parallel agent execution
- [ ] Add error handling and retries
- [ ] Create result aggregation logic
- [ ] Test end-to-end agent pipeline

#### 3.2 API Endpoints (still pipeline-first)
- [ ] Implement upload endpoint (in-memory storage)
- [ ] Implement status endpoint (in-memory state)
- [ ] Implement insights endpoint (from in-memory pipeline results)
- [ ] Add file validation
- [ ] Add async processing support

#### 3.3 Vector Store Integration (persistence phase)
- [ ] Set up FAISS vector store
- [ ] Implement embedding generation
- [ ] Create vector storage logic
- [ ] Link vectors to database records (enable persistence)
- [ ] Test vector operations

### Phase 4: RAG & Search (Week 4)

#### 4.1 RAG Implementation
- [ ] Design RAG query pipeline
- [ ] Implement semantic search
- [ ] Create context retrieval logic
- [ ] Add ranking and filtering
- [ ] Test search accuracy

#### 4.2 Search API
- [ ] Implement search endpoint
- [ ] Add query preprocessing
- [ ] Create result formatting
- [ ] Add pagination support
- [ ] Test search functionality

### Phase 5: Testing & Optimization (Week 5)

#### 5.1 Testing
- [ ] Write unit tests for all agents
- [ ] Write integration tests for API
- [ ] Write end-to-end pipeline tests
- [ ] Add performance tests
- [ ] Achieve >80% code coverage

#### 5.2 Optimization
- [ ] Profile performance bottlenecks
- [ ] Optimize agent execution
- [ ] Add caching where appropriate
- [ ] Optimize database queries
- [ ] Improve error messages

### Phase 6: Deployment & Documentation (Week 6)

#### 6.1 Docker Configuration
- [ ] Optimize Dockerfile
- [ ] Configure docker-compose.yml
- [ ] Add volume mounts
- [ ] Test containerized deployment

---

## Setup Instructions

### Prerequisites

1. **Python 3.10+** (recommended: 3.11)
2. **Docker & Docker Compose** (latest stable)
3. **Git** (for version control)
4. **PostgreSQL 15+** (or use Docker)
5. **CUDA-capable GPU** (optional, for faster Whisper/LLM inference)

### Step-by-Step Setup

#### 1. Clone and Navigate
```bash
cd nlp_project
```

#### 2. Create Virtual Environment (root)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies (root)
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Environment Configuration
```bash
# Create .env file with your configuration
# See environment variables section below for required settings
```

Required environment variables:
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/meeting_insights

# LLM Configuration
MISTRAL_API_KEY=your_mistral_api_key  # If using Mistral API
LLM_MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.2  # Or local path
USE_LOCAL_LLM=true  # Set to false for API-based models

# Whisper Configuration
WHISPER_MODEL=large-v3  # or medium, base, etc.
WHISPER_DEVICE=cuda  # or cpu

# Vector Store
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_PATH=./storage/vectors

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Storage Paths (relative to backend directory)
STORAGE_BASE_PATH=./storage          # Base storage directory
MEETING_STORAGE_PATH=./storage/{meeting_id}  # Per-meeting storage (use {meeting_id} placeholder)
VECTOR_STORE_PATH=./storage/vectors  # Global vector store (shared across meetings)
MAX_FILE_SIZE_MB=500                 # Maximum audio file size in MB
```

#### 5. Start PostgreSQL with Docker
```bash
cd backend
docker-compose up -d postgres
```

#### 6. Initialize Database
```bash
# Run migrations
alembic upgrade head

# Or use setup script
python scripts/setup_db.py
```

#### 7. Download Whisper Model (if not auto-downloading)
```bash
python -c "import whisper; whisper.load_model('large-v3')"
```

#### 8. Start Application
```bash
# Development mode (from root with venv activated)
uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000

# Or from backend directory
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or with Docker Compose (from backend directory)
cd backend
docker-compose up
```

#### 9. Verify Installation
```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

---

## Development Workflow

### Code Organization Principles

1. **Separation of Concerns**: API, services, agents, and models are separate layers
2. **Dependency Injection**: Use FastAPI's dependency system
3. **Async First**: Use async/await for I/O operations
4. **Type Hints**: Use type hints throughout for better IDE support
5. **Error Handling**: Consistent error handling with custom exceptions

### Coding Standards

1. **Formatting**: Use `black` with line length 100
2. **Linting**: Use `flake8` with project-specific rules
3. **Type Checking**: Use `mypy` for static type checking
4. **Imports**: Use absolute imports, organize with `isort`

---

## Testing Strategy

### Test Structure

```
tests/
├── unit/              # Fast, isolated unit tests
├── integration/       # Component integration tests
└── fixtures/          # Test data and mocks
```

### Test Coverage Goals

- **Unit Tests**: >90% coverage for agents and services
- **Integration Tests**: All API endpoints and critical workflows
- **End-to-End Tests**: Complete pipeline from upload to insights

---

## Deployment Guide

### Docker Deployment

#### Build Image
```bash
docker build -t meeting-insight-generator:latest .
```

#### Run with Docker Compose
```bash
docker-compose up -d
```

#### Environment-Specific Configs
- Development: `docker-compose.yml`
- Production: `docker-compose.prod.yml` (to be created)

### Production Considerations

1. **Resource Requirements**:
   - CPU: 4+ cores recommended
   - RAM: 16GB+ (32GB for large models)
   - GPU: Optional but recommended for faster processing
   - Storage: 100GB+ for audio files and vectors

2. **Scaling**:
   - Use async workers (Celery or similar) for processing
   - Implement queue system for uploads
   - Consider cloud storage for audio files

3. **Monitoring**:
   - Add logging to all components
   - Implement health checks
   - Set up error tracking (Sentry, etc.)

4. **Security**:
   - Use environment variables for secrets
   - Implement API authentication
   - Validate all inputs
   - Rate limiting on API endpoints

---

## Next Steps

1. Review this guide and adjust based on your specific needs
2. Set up the repository structure
3. Begin Phase 1 implementation
4. Iterate based on testing and feedback

---

## Additional Resources

---

## Frontend Plan (React)

### Goals
- Provide a minimal, functional UI to:
  - Upload audio/video files to the backend (`/api/v1/upload`)
  - Poll processing status (`/api/v1/status/{meeting_id}`)
  - Display results/insights (`/api/v1/insights/{meeting_id}`)
- Keep it lightweight (no design system required); focus on functionality and clarity.

### Tech Stack
- React (TypeScript) via Vite or Create React App (Vite recommended for speed)
- HTTP client: `fetch` (or `axios` if preferred)
- State: React hooks; no global state library required for MVP
- UI: Minimal components (no heavy UI kit needed)

### Planned Structure (frontend/)
```
frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── public/
│   └── index.html
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── api/
    │   └── client.ts          # fetch helpers for upload/status/insights
    ├── components/
    │   ├── UploadForm.tsx     # file picker + submit
    │   ├── StatusPoller.tsx   # polls status endpoint
    │   └── InsightsViewer.tsx # renders transcript + stub agent outputs
    ├── hooks/
    │   └── usePolling.ts      # generic polling hook
    └── types/
        └── api.ts             # Type definitions for API responses
```

### Frontend Flows
1) Upload:
   - User selects file (audio/video).
   - POST `/api/v1/upload` (multipart/form-data).
   - Receive `meeting_id`, set UI to “queued/processing.”
2) Poll status:
   - Poll `/api/v1/status/{meeting_id}` every 2–3s until `completed` or `error`.
3) Fetch insights:
   - GET `/api/v1/insights/{meeting_id}` when status is `completed`.
   - Render transcript text, segments, and agent outputs (topic/decision/action/sentiment/summary stubs).
4) Display:
   - Show transcript text.
   - Show lists/tables for extracted items (even if stubbed).
   - Show statuses/errors clearly.

### Environment & Config
- Frontend `.env` (e.g., `.env.local`):
  - `VITE_API_BASE_URL=http://localhost:8000` (point to backend)
- CORS: Already enabled in backend (wide open). For production, restrict origins to the deployed frontend domain.

### Tasks to Implement Frontend
- [ ] Scaffold React app in `frontend/` (Vite + TS).
- [ ] Add API client helpers (`upload`, `getStatus`, `getInsights`).
- [ ] Build components:
  - [ ] `UploadForm` (file input + submit)
  - [ ] `StatusPoller` (polls backend)
  - [ ] `InsightsViewer` (renders transcript and stub agent outputs)
- [ ] Add basic routing (optional; single-page is fine).
- [ ] Add minimal styling (plain CSS or simple utility).
- [ ] Add error/loading states and file-type/size validation (audio/video).
- [ ] Add `.env` guidance and README section for frontend.
- [ ] Connect to backend endpoints and verify end-to-end flow.
- [ ] Add a simple integration test (manual or Cypress later).

### How to Run (planned)
```bash
cd frontend
npm install
npm run dev    # or npm run build && npm run preview
```

### Backend Expectations for Frontend
- Endpoints used:
  - POST `/api/v1/upload`
  - GET `/api/v1/status/{meeting_id}`
  - GET `/api/v1/insights/{meeting_id}`
- Response shapes (current stubs):
  - `/upload`: `{ meeting_id, status }`
  - `/status/{id}`: `{ meeting_id, status }`
  - `/insights/{id}`: `{ meeting_id, insights: { transcript, topics, decisions, action_items, sentiments, summary } }`
- Note: Agent outputs are stubbed; shapes may evolve once real LLM logic is added.

### Open Items / Constraints
- Video handling: backend can likely extract audio via ffmpeg, but needs explicit validation/testing.
- Auth: not implemented; endpoints are open. For production, add auth and tighten CORS.
- Persistence: currently in-memory + filesystem; DB/FAISS planned later—frontend should tolerate missing history persistence for now.


- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Whisper GitHub](https://github.com/openai/whisper)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**Last Updated**: [Current Date]
**Version**: 1.0

