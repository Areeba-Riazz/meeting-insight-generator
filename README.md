# Meeting Insight Generator

The Meeting Insight Generator is an AI-powered backend system that converts meeting audio into structured, actionable insights. It goes beyond basic transcription by identifying decisions, action items, responsibilities, discussion topics, and sentiments. The system also provides semantic search across past meetings using vector embeddings, enabling teams to quickly recall important discussions and decisions.

## 📚 Documentation

- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Complete implementation guide with tech stack, architecture, and step-by-step phases

## ✅ Current Status

- Phase 1 completed: repo restructured (backend/frontend), shared root venv setup, Docker configs, base FastAPI app with CORS, health endpoint, and starter request/response models. Persistence (Postgres/FAISS) is deferred to later phases per plan.

## ✨ Key Features

- **High-accuracy transcription** using OpenAI Whisper
- **Intelligent topic segmentation** - Automatically identifies conversation topics
- **Decision extraction** - Identifies key decisions and participants
- **Action item detection** - Extracts tasks, assignees, and deadlines
- **Sentiment analysis** - Analyzes emotional tone and engagement
- **Summary generation** - Creates executive summaries
- **Semantic search** - Search across historical meetings using RAG
- **REST API** - Well-documented API for integration
- **Multi-agent architecture** - Specialized AI agents for different analysis tasks

## 🏗️ Architecture Overview

```
Audio Input → Whisper Transcription → Multi-Agent Processing → Structured Insights
                                      ↓
                              Vector Store (FAISS)
                                      ↓
                              Historical Search (RAG)
```

### Multi-Agent Processing
- **Topic Agent** - Identifies conversation segments and topics
- **Decision Agent** - Extracts decisions with context
- **Action Item Agent** - Identifies tasks and responsibilities
- **Sentiment Agent** - Analyzes emotional tone
- **Summary Agent** - Generates executive summaries

## 🛠️ Technology Stack

- **Framework**: FastAPI (Python)
- **Agent Framework**: LangChain
- **LLMs**: Mistral-7B / LLaMA 3.1
- **Speech Recognition**: OpenAI Whisper
- **Vector Database**: FAISS
- **Database**: PostgreSQL
- **Containerization**: Docker & Docker Compose

See [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for detailed technology stack information.

## 📋 Prerequisites

- Python 3.10+
- Docker & Docker Compose
- 16GB+ RAM (32GB recommended for local LLMs)
- GPU with CUDA (optional but recommended)

## 🚦 Getting Started

1. **Clone the repository**
   ```bash
   cd meeting-insight-generator-main
   ```

2. **Set up environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   # Create .env file with your configuration
   # See IMPLEMENTATION_GUIDE.md for required environment variables
   ```

4. **Start services**
   ```bash
   cd backend
   docker-compose up -d postgres
   uvicorn src.main:app --reload
   ```

5. **Access API docs**
   ```
   http://localhost:8000/docs
   ```

## 📁 Project Structure

```
nlp_project/
├── backend/                # Backend API application
│   ├── src/               # Main source code
│   │   ├── api/           # API endpoints
│   │   ├── agents/        # AI agents
│   │   ├── services/      # Business logic
│   │   ├── models/        # Database models
│   │   └── utils/         # Utilities
│   ├── tests/             # Test suite
│   ├── scripts/           # Utility scripts
│   ├── migrations/        # Database migrations
│   └── storage/           # Local storage (per-meeting folders)
├── frontend/              # Frontend application
└── Documentation/         # Project documentation
```

See [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for detailed repository structure.

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_agents/
```

## 🐳 Docker Deployment

```bash
cd backend

# Build and start all services
docker-compose up --build

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

**Note**: Docker build context is set to parent directory to access `requirements.txt` at root.

## 📖 API Endpoints

- `POST /api/v1/upload` - Upload audio file
- `GET /api/v1/status/{meeting_id}` - Check processing status
- `GET /api/v1/insights/{meeting_id}` - Retrieve insights
- `POST /api/v1/search` - Semantic search across meetings

Full API documentation available at `/docs` when the server is running.

## 🤝 Contributing

1. Follow the coding standards (black, flake8, mypy)
2. Write tests for new features
3. Update documentation as needed
4. Use conventional commits

## 📝 License

MIT License

## 🔗 Resources

- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Whisper GitHub](https://github.com/openai/whisper)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
