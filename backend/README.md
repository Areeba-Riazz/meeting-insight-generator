# Backend - Meeting Insight Generator

This is the backend API for the Meeting Insight Generator project.

## Quick Start

See the main [README.md](../README.md) and [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md) for setup instructions.

## Structure

- `src/` - Main application source code
- `tests/` - Test suite
- `scripts/` - Utility scripts
- `migrations/` - Database migrations
- `storage/` - Local file storage

## Running the Application

```bash
# From project root, activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# From backend directory
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# One-line launcher
python main.py
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

