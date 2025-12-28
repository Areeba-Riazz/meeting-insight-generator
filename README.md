# Meeting Insight Generator

> **Course Project**: This project was developed as part of a Natural Language Processing (NLP) course, demonstrating practical application of NLP techniques including speech recognition, LLM integration, semantic search, and multi-agent AI systems.

An AI-powered system that converts meeting audio/video into structured, actionable insights. The system goes beyond basic transcription by identifying decisions, action items, responsibilities, discussion topics, and sentiments. It also provides semantic search across past meetings using vector embeddings and an interactive chat interface with RAG (Retrieval Augmented Generation) for AI assistance.

## 🚀 Key Features

- **High-Accuracy Transcription**: Uses WhisperX (OpenAI Whisper enhanced) for audio-to-text conversion with speaker diarization via pyannote.audio
- **Multi-Agent AI System**: Five specialized agents extract insights:
  - **Topic Agent**: Segments meetings into coherent topics with timestamps and summaries
  - **Decision Agent**: Identifies explicit and implicit decisions with participants and rationale
  - **Action Item Agent**: Extracts tasks with assignees and deadlines, handling implicit assignments
  - **Sentiment Agent**: Analyzes sentiment per segment using HuggingFace models with fallback NLP techniques
  - **Summary Agent**: Generates executive summaries with key quotes and actionable information
- **Intelligent Chatbot**: Floating AI assistant with RAG integration that:
  - Performs semantic search across meeting content to answer questions
  - Provides project-scoped or global search capabilities
  - Analyzes and synthesizes meeting data to answer complex queries
  - Cites sources from relevant meeting segments
- **Semantic Search**: Vector-based search across all meeting content using FAISS with sentence-transformers embeddings
- **Project Management**: Organize meetings into projects with full CRUD operations via PostgreSQL
- **REST API**: Complete API for upload, status tracking, insights retrieval, search, and chat
- **Modern Frontend**: React-based UI with real-time status updates, insights visualization, and interactive chat
- **Monitoring**: Prometheus metrics for performance monitoring and observability
- **Comprehensive Testing**: Unit, integration, E2E, and performance tests with 84% code coverage

## 🏗️ Architecture Overview

The system follows a 3-tier architecture:

**Presentation Tier**: React frontend with TypeScript, providing upload interface, insights viewer, project management, search, and floating chat interface.

**Business Logic Tier**: FastAPI backend with:
- Agent Orchestrator managing the processing pipeline
- Five specialized AI agents with LLM integration and rule-based fallbacks
- Transcription service using WhisperX with speaker diarization
- Vector store service for semantic search
- Database service layer for CRUD operations
- Chat service with RAG (Retrieval Augmented Generation)

**Data Access Tier**: 
- PostgreSQL database for structured data storage
- File system for audio files, transcripts, and insights JSON
- FAISS vector store for semantic search embeddings

```
Audio/Video Input
    ↓
WhisperX Transcription (with pyannote speaker diarization)
    ↓
Agent Orchestrator → Multi-Agent Processing Pipeline
    ├──► Topic Agent (LLM + TF-IDF fallback)
    ├──► Decision Agent (Groq API + pattern matching)
    ├──► Action Item Agent (LLM + regex patterns)
    ├──► Sentiment Agent (HuggingFace + NLP fallback)
    └──► Summary Agent (LLM + extractive fallback)
    ↓
Storage Layer
    ├──► PostgreSQL Database (projects, meetings, insights)
    ├──► File System (audio, transcripts, JSON)
    └──► FAISS Vector Store (embeddings for search)
    ↓
Access Layer
    ├──► REST API (upload, status, insights, search, chat)
    ├──► Semantic Search (vector similarity)
    └──► Chat Interface (RAG-powered AI assistant)
```

## 🤖 AI Agents & LLM Integration

Each agent implements specialized extraction with LLM-based primary logic and rule-based fallbacks:

- **Topic Agent**: Uses LLM to identify topic boundaries with summaries. Fallback employs sliding window TF-IDF to detect vocabulary shifts indicating topic changes.

- **Decision Agent**: Integrates with Groq API for fast inference. Identifies explicit ("we decided") and implicit decisions through consensus detection. Pattern-based fallback searches decision markers and extracts context windows.

- **Action Item Agent**: Extracts tasks with assignee and deadline extraction. Handles implicit assignees ("can you", "please") and relative dates ("next week", "by Friday") through date parsing logic. Regex fallback matches common action patterns.

- **Sentiment Agent**: Uses HuggingFace cardiffnlp/twitter-roberta-base-sentiment model processing 512-token segments. Applies negation detection and contrastive conjunction handling. Fallback employs lexicon-based scoring with intensity modifiers.

- **Summary Agent**: Three-stage process: (1) Extract key points per topic, (2) Synthesize narrative focusing on actionable information, (3) Identify impactful quotes with speaker attribution. Fallback uses extractive summarization with sentence scoring.

- **LLM Client**: Unified client supports multiple providers (Mistral, Groq) with automatic failover. Response caching reduces repeated API calls. Retry logic handles transient failures with exponential backoff (max 3 retries: 1-2-4 second delays).

## 💬 Chatbot with RAG

The interactive chatbot provides AI assistance with Retrieval Augmented Generation (RAG):

- **Semantic Search Integration**: Automatically searches vector store for relevant meeting content based on user queries
- **Context-Aware Responses**: Uses retrieved meeting data to provide informed answers
- **Project-Scoped Search**: Can limit search to specific projects or search globally
- **Source Citation**: Displays sources from relevant meeting segments
- **Intelligent Analysis**: Synthesizes information across multiple meetings to answer complex questions
- **Floating UI**: Always-accessible chat interface integrated into the frontend

## 📊 Database Schema

The system uses PostgreSQL with 10 database tables:

- `projects` - Project metadata and organization
- `meetings` - Meeting metadata, status, and file information
- `transcripts` - Full transcript text with model information
- `transcript_segments` - Timestamped segments with speaker attribution
- `topics` - Topic segments with summaries and time ranges
- `decisions` - Extracted decisions with participants and rationale
- `action_items` - Tasks with assignees, due dates, and status
- `sentiment_analyses` - Overall sentiment scores per meeting
- `sentiment_segments` - Per-segment sentiment analysis
- `summaries` - Meeting summaries

The system supports hybrid storage: database preferred with filesystem fallback for backward compatibility.

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern async web framework with automatic API documentation
- **SQLAlchemy** - ORM with async support and connection pooling
- **PostgreSQL** - Primary database (optional, with filesystem fallback)
- **WhisperX** - Enhanced Whisper with alignment and diarization
- **pyannote.audio** - Speaker diarization pipeline
- **FAISS** - Vector similarity search for semantic search
- **sentence-transformers** - Embedding generation (all-MiniLM-L6-v2)
- **HuggingFace Transformers** - Sentiment analysis models
- **Mistral AI / Groq** - LLM providers for agent processing
- **Prometheus Client** - Metrics collection and monitoring

### Frontend
- **React** - UI framework with hooks
- **TypeScript** - Type safety and better developer experience
- **Vite** - Fast build tool and dev server
- **React Router** - Client-side navigation
- **Lucide React** - Icon library

## 📦 Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (optional, for database features)
- FFmpeg (for video processing)

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd nlp_project
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
cd backend
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file in the `backend/` directory:
```env
# Database (optional - system works without it)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/meeting_insights

# LLM Configuration
MISTRAL_API_KEY=your_mistral_api_key_here  # Optional, uses mock responses if not set
GROQ_API_KEY=your_groq_api_key_here  # Optional, for Decision Agent
MODEL_TYPE=mistral

# Whisper Configuration
WHISPER_MODEL=small  # or medium, large-v3, etc.
WHISPER_DEVICE=cpu  # or cuda
HUGGINGFACE_TOKEN=your_huggingface_token  # For speaker diarization

# Vector Store
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_PATH=./storage/vectors

# API Configuration
API_HOST=0.0.0.0
API_PORT=3000
DEBUG=true

# Storage Paths
STORAGE_BASE_PATH=./storage
MAX_FILE_SIZE_MB=500
```

5. **Initialize Database (Optional)**
```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Run database setup
python scripts/setup_db.py
```

6. **Start the backend server**
```bash
# From backend directory
uvicorn main:app --reload --host 0.0.0.0 --port 3000

# Or from root
cd backend && uvicorn main:app --reload
```

### Frontend Setup

1. **Install dependencies**
```bash
cd frontend
npm install
```

2. **Configure environment**
Create a `.env.local` file in the `frontend/` directory:
```env
VITE_API_BASE_URL=http://localhost:3000
```

3. **Start development server**
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 📡 API Endpoints

### Core Endpoints
- `POST /api/v1/upload` - Upload meeting audio/video file
- `GET /api/v1/status/{meeting_id}` - Get processing status
- `GET /api/v1/insights/{meeting_id}` - Retrieve meeting insights
- `POST /api/v1/search` - Semantic search across meetings
- `GET /api/v1/search/stats` - Get vector store statistics

### Project Management
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Project Meetings
- `GET /api/v1/projects/{project_id}/meetings` - List meetings in project
- `GET /api/v1/projects/{project_id}/meetings/{meeting_id}` - Get meeting details
- `DELETE /api/v1/projects/{project_id}/meetings/{meeting_id}` - Delete meeting

### Chat
- `POST /api/v1/chat` - Chat with AI assistant

### Health & Monitoring
- `GET /health` - Health check endpoint
- `GET /` - API information and documentation
- `GET /metrics` - Prometheus metrics endpoint (requires prometheus-client)

## 🎯 Usage

1. **Upload a Meeting**: Use the upload page to submit an audio or video file
2. **Track Progress**: Monitor processing status in real-time
3. **View Insights**: Explore transcript, topics, decisions, action items, sentiment, and summary
4. **Search**: Use semantic search to find relevant content across all meetings
5. **Organize**: Create projects to group related meetings
6. **Chat**: Click the floating chat icon for AI assistance

## 🧪 Testing

The project includes comprehensive test coverage with 58 tests achieving 84% code coverage.

### Test Structure
- **Unit Tests** (39 tests): Fast, isolated tests for individual agents and components
- **Integration Tests** (13 tests): API endpoint tests with mocked dependencies
- **E2E Tests** (3 tests): Full pipeline workflow tests
- **Performance Tests** (3 tests): Performance benchmarks and load testing

### Running Tests
```bash
# Run all tests
cd backend
pytest

# Run with coverage report
pytest --cov=src --cov-report=html
pytest --cov=src --cov-report=term-missing

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration  # Integration tests only
pytest -m e2e          # End-to-end tests only
pytest -m performance # Performance tests only

# Run specific test file
pytest tests/unit/test_agents/test_topic_agent.py

# Run with verbose output
pytest -v
```

### Test Scripts
```bash
# Run tests with coverage report
python scripts/run_tests.py

# Profile performance
python scripts/profile_performance.py
```

### Coverage Goals
- **Target**: >80% code coverage
- **Current**: 84% overall coverage
- **Breakdown by Component**:
  - Backend API Routes: 92%
  - Topic Agent: 92%
  - Decision Agent: 88%
  - Action Item Agent: 90%
  - Sentiment Agent: 85%
  - Summary Agent: 87%

## 📊 Monitoring with Prometheus

The system includes optional Prometheus monitoring for observability and performance tracking.

### Available Metrics
- **HTTP Metrics**: Request counts and duration by endpoint
- **Meeting Processing**: Processing duration and success/error rates by stage
- **Agent Execution**: Execution times and success rates per agent
- **Vector Store**: Search request counts and duration (ready for implementation)
- **Database**: Query counts and duration (ready for implementation)

### Setup
```bash
# Install Prometheus client (optional - app works without it)
pip install prometheus-client

# Metrics are automatically collected when available
# Access metrics endpoint
curl http://localhost:3000/metrics
```

### Prometheus Configuration
The system gracefully handles missing Prometheus - all metrics are optional and don't break functionality if the library is not installed. Metrics are collected automatically when available.

### Viewing Metrics
- Access `/metrics` endpoint in browser: `http://localhost:3000/metrics`
- Configure Prometheus server to scrape the endpoint
- Optionally set up Grafana for visualization

## 🧹 Code Quality

### Backend
```bash
# Format code
black backend/src

# Lint code
flake8 backend/src

# Type checking
mypy backend/src
```

### Frontend
```bash
cd frontend
npm run lint
npm run type-check
```

## 📝 Project Structure

```
nlp_project/
├── backend/
│   ├── src/
│   │   ├── api/          # API routes and models
│   │   ├── agents/       # AI agents (topic, decision, etc.)
│   │   ├── core/         # Core configuration (database, settings)
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic services
│   │   └── utils/        # Utility functions
│   ├── storage/          # File storage (meetings, vectors)
│   ├── scripts/          # Setup and utility scripts
│   └── main.py           # Application entry point
├── frontend/
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   └── types/        # TypeScript types
│   └── package.json
└── README.md
```

## 📡 API Documentation

Interactive API documentation is automatically generated by FastAPI:
- **Swagger UI**: `http://localhost:3000/docs`
- **ReDoc**: `http://localhost:3000/redoc`
- **OpenAPI Schema**: `http://localhost:3000/openapi.json`

## 👥 Project Team

This project was developed as part of the Natural Language Processing course.

**Team Members:**
- Hafsa Imtiaz - i220959
- Umer Farooq - i221007
- Areeba Riaz - i221244
- Zayyam Hassan - i221247
- Muhammad Rayyan - i221022
- Abeer Jawad - i221041
