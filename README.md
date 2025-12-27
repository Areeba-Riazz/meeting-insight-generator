# Meeting Insight Generator

An AI-powered system that converts meeting audio/video into structured, actionable insights. The system goes beyond basic transcription by identifying decisions, action items, responsibilities, discussion topics, and sentiments. It also provides semantic search across past meetings using vector embeddings and an interactive chat interface for AI assistance.

## 🚀 Key Features

- **High-Accuracy Transcription**: Uses OpenAI Whisper for audio-to-text conversion with speaker diarization
- **AI-Powered Analysis**: Multi-agent system extracts:
  - Topic segmentation
  - Decisions and responsibilities
  - Action items with assignees and deadlines
  - Sentiment analysis
  - Executive summaries
- **Semantic Search**: Vector-based search across all meeting content using FAISS
- **Project Management**: Organize meetings into projects with full CRUD operations
- **Interactive Chat**: Floating AI assistant chat interface for real-time help
- **REST API**: Complete API for upload, status tracking, insights retrieval, and search
- **Modern Frontend**: React-based UI with real-time status updates and insights visualization

## 🏗️ Architecture Overview

```
Audio/Video Input
    ↓
Whisper Transcription (with speaker diarization)
    ↓
Multi-Agent Processing Pipeline
    ├──► Topic Agent
    ├──► Decision Agent
    ├──► Action Item Agent
    ├──► Sentiment Agent
    └──► Summary Agent
    ↓
Vector Store (FAISS) + PostgreSQL Database
    ↓
Structured JSON Output + Semantic Search
```

## 📊 Database Implementation Status

**Database is fully implemented** with the following components:

### ✅ Completed:
- **10 Database Tables**: Fully defined SQLAlchemy models
  - `projects` - Project metadata
  - `meetings` - Meeting metadata and status
  - `transcripts` - Full transcript text
  - `transcript_segments` - Timestamped transcript segments with speakers
  - `topics` - Topic segments with summaries
  - `decisions` - Extracted decisions with participants and rationale
  - `action_items` - Tasks with assignees and due dates
  - `sentiment_analyses` - Overall sentiment scores
  - `sentiment_segments` - Per-segment sentiment analysis
  - `summaries` - Meeting summaries

- **Database Service Layer**: Complete CRUD operations for all models
- **Connection Management**: Async SQLAlchemy with connection pooling
- **Auto-Initialization**: Tables auto-created on startup (graceful fallback if DB unavailable)
- **Project Management**: Fully integrated with database (projects API routes)
- **Hybrid Storage**: System works with or without database (filesystem fallback for backward compatibility)

### 📝 Current State:
- Projects API: **Fully database-integrated**
- Upload/Insights API: **Hybrid mode** (database preferred, filesystem fallback)
- Vector Store: **Filesystem-based** (FAISS index files)
- The system can run in filesystem-only mode for development/testing

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern async web framework
- **SQLAlchemy** - ORM with async support
- **PostgreSQL** - Primary database (optional, with filesystem fallback)
- **Whisper** - OpenAI's speech recognition model
- **LangChain** - LLM orchestration framework
- **FAISS** - Vector similarity search
- **sentence-transformers** - Embedding generation

### Frontend
- **React** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Router** - Navigation
- **Lucide React** - Icons

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
MODEL_TYPE=mistral

# Whisper Configuration
WHISPER_MODEL=small  # or medium, large-v3, etc.
WHISPER_DEVICE=cpu  # or cuda

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
- `GET /health` - Health check
- `GET /` - API info
- `GET /metrics` - Prometheus metrics endpoint (optional, requires prometheus-client)

## 🎯 Usage

1. **Upload a Meeting**: Use the upload page to submit an audio or video file
2. **Track Progress**: Monitor processing status in real-time
3. **View Insights**: Explore transcript, topics, decisions, action items, sentiment, and summary
4. **Search**: Use semantic search to find relevant content across all meetings
5. **Organize**: Create projects to group related meetings
6. **Chat**: Click the floating chat icon for AI assistance

## 🧪 Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality
```bash
# Backend formatting
black backend/src
flake8 backend/src

# Frontend formatting
cd frontend
npm run lint
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

## 🔒 Security Notes

- API endpoints are currently open (no authentication)
- For production, add authentication and restrict CORS origins
- Store API keys securely (use environment variables)
- Validate and sanitize all user inputs

## 📄 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📚 Documentation

- See `IMPLEMENTATION_GUIDE.md` for detailed architecture documentation
- API documentation available at `/docs` when server is running
