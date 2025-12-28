# API Documentation

## Overview

The Meeting Insight Generator API is a RESTful service for processing meeting recordings and extracting insights. The API allows you to upload video/audio files, which are automatically transcribed and analyzed to extract summaries, topics, decisions, action items, and sentiment analysis.

The API supports project-based organization, allowing you to group meetings into projects for better management. Once processed, meetings can be searched semantically using natural language queries, and you can interact with an AI assistant that uses RAG (Retrieval Augmented Generation) to answer questions about your meetings.

All endpoints return JSON responses and follow standard HTTP status codes. The API processes files asynchronously in the background, providing status updates throughout the processing pipeline.

## Table of Contents

- [Base URL](#base-url)
- [API Routes](#api-routes)
  - [Health & Monitoring](#health--monitoring)
  - [Projects](#projects)
  - [Project Meetings](#project-meetings)
  - [Upload & Processing](#upload--processing)
  - [Search](#search)
  - [Chat](#chat)
  - [Static Files](#static-files)
- [External API Calls](#external-api-calls)
- [Notes](#notes)

---

## Base URL

| Environment | URL |
|------------|-----|
| **Development** | `http://localhost:3000` |
| **Production** | Configure via `API_BASE_URL` environment variable |

---

## API Routes

### Health & Monitoring

#### `GET /`

Root endpoint - service information.

**Response** `200 OK`:
```json
{
  "status": "ok",
  "service": "Meeting Insight Generator API",
  "host": "0.0.0.0",
  "port": 3000
}
```

---

#### `GET /health`

Health check endpoint.

**Response** `200 OK`:
```json
{
  "status": "ok"
}
```

---

#### `GET /api/v1/health`

Alternative health check endpoint.

**Response** `200 OK`:
```json
{
  "status": "ok"
}
```

---

#### `GET /metrics`

Prometheus metrics endpoint.

**Response** `200 OK`:
- **Content-Type**: `text/plain`
- **Body**: Prometheus-formatted metrics

---

### Projects

#### `POST /api/v1/projects`

Create a new project.

**Request Body**:
```json
{
  "name": "string (required)",
  "description": "string (optional)"
}
```

**Response** `201 Created`:
```json
{
  "id": "uuid",
  "name": "Project Name",
  "description": "Project description",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "meetings_count": 0
}
```

---

#### `GET /api/v1/projects`

List all projects.

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | `int` | `0` | Pagination offset |
| `limit` | `int` | `100` | Results per page (max: 1000) |

**Response** `200 OK`:
```json
{
  "projects": [
    {
      "id": "uuid",
      "name": "Project Name",
      "description": "Project description",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00",
      "meetings_count": 5
    }
  ],
  "total": 1
}
```

---

#### `GET /api/v1/projects/{project_id}`

Get project by ID.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | `UUID` | Project identifier |

**Response** `200 OK`:
```json
{
  "id": "uuid",
  "name": "Project Name",
  "description": "Project description",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "meetings_count": 5
}
```

---

#### `PUT /api/v1/projects/{project_id}`

Update project.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | `UUID` | Project identifier |

**Request Body**:
```json
{
  "name": "string (optional)",
  "description": "string (optional)"
}
```

**Response** `200 OK`:
```json
{
  "id": "uuid",
  "name": "Updated Project Name",
  "description": "Updated description",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "meetings_count": 5
}
```

---

#### `DELETE /api/v1/projects/{project_id}`

Delete project (cascades to meetings).

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | `UUID` | Project identifier |

**Response** `204 No Content`

---

### Project Meetings

#### `GET /api/v1/projects/{project_id}/meetings`

List meetings in a project.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | `UUID` | Project identifier |

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | `int` | `0` | Pagination offset |
| `limit` | `int` | `100` | Results per page (max: 1000) |
| `status` | `string` | `null` | Filter by status (optional) |

**Response** `200 OK`:
```json
{
  "meetings": [
    {
      "id": "uuid",
      "project_id": "uuid",
      "meeting_name": "Meeting Name",
      "original_filename": "meeting.mp4",
      "file_size_bytes": 1048576,
      "content_type": "video/mp4",
      "status": "completed",
      "upload_timestamp": "2024-01-01T00:00:00",
      "processing_completed_at": "2024-01-01T00:05:00",
      "has_insights": true,
      "has_transcript": true
    }
  ],
  "total": 1
}
```

---

#### `GET /api/v1/projects/{project_id}/meetings/{meeting_id}`

Get meeting details.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | `UUID` | Project identifier |
| `meeting_id` | `UUID` | Meeting identifier |

**Response** `200 OK`:
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "meeting_name": "Meeting Name",
  "original_filename": "meeting.mp4",
  "file_size_bytes": 1048576,
  "content_type": "video/mp4",
  "status": "completed",
  "upload_timestamp": "2024-01-01T00:00:00",
  "processing_completed_at": "2024-01-01T00:05:00",
  "has_insights": true,
  "has_transcript": true
}
```

---

#### `DELETE /api/v1/projects/{project_id}/meetings/{meeting_id}`

Delete meeting (cascades to insights).

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | `UUID` | Project identifier |
| `meeting_id` | `UUID` | Meeting identifier |

**Response** `204 No Content`

---

### Upload & Processing

#### `POST /api/v1/upload`

Upload meeting video/audio file.

**Content-Type**: `multipart/form-data`

**Form Data**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | `File` | Yes | Video/audio file (max 500MB) |

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | `UUID` | No | Project UUID to associate meeting with |

**Supported Formats**: MP4, MP3, WAV, M4A, etc.

**Response** `200 OK`:
```json
{
  "meeting_id": "uuid or legacy_id",
  "status": "uploading"
}
```

> **Note**: Processing starts automatically in background after upload.

---

#### `GET /api/v1/status/{meeting_id}`

Get processing status for a meeting.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | `UUID` or `string` | Meeting identifier (UUID or legacy folder name) |

**Response** `200 OK`:
```json
{
  "meeting_id": "string",
  "status": "uploading|processing|completed|error",
  "progress": 75.5,
  "stage": "Processing transcript",
  "estimated_time_remaining": null
}
```

**Status Values**:
- `uploading` - File is being uploaded
- `processing` - File is being processed
- `completed` - Processing completed successfully
- `error` - Processing failed

---

#### `GET /api/v1/insights/{meeting_id}`

Get meeting insights.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `meeting_id` | `UUID` or `string` | Meeting identifier (UUID or legacy folder name) |

**Response** `200 OK`:
```json
{
  "meeting_id": "string",
  "insights": {
    "transcript": {
      "text": "Full transcript text...",
      "segments": [...]
    },
    "topics": [
      {
        "topic": "Topic name",
        "description": "Topic description"
      }
    ],
    "decisions": [
      {
        "decision": "Decision text",
        "timestamp": 120.5
      }
    ],
    "action_items": [
      {
        "action": "Action item text",
        "assignee": "Person name"
      }
    ],
    "summary": "Meeting summary text...",
    "sentiment": {
      "overall": "positive",
      "breakdown": {...}
    }
  },
  "legacy_meeting_id": "string (optional)",
  "file_path": "string (optional)",
  "original_filename": "string (optional)"
}
```

---

#### `GET /api/v1/meetings`

List all meetings (legacy endpoint).

**Response** `200 OK`:
```json
{
  "meetings": [
    {
      "meeting_id": "meeting_folder_name",
      "uuid": "uuid",
      "meeting_name": "Meeting Name",
      "upload_timestamp": "2024-01-01T00:00:00",
      "file_info": {
        "original_filename": "meeting.mp4",
        "size_bytes": 1048576,
        "content_type": "video/mp4"
      },
      "has_insights": true,
      "has_transcript": true
    }
  ]
}
```

---

### Search

#### `POST /api/v1/search`

Semantic search across meeting content.

**Request Body**:
```json
{
  "query": "string (required, 1-500 chars)",
  "top_k": 10,
  "segment_types": ["transcript", "topic", "decision", "action_item", "summary"],
  "meeting_ids": ["meeting_id_1", "meeting_id_2"],
  "project_id": "uuid (optional)",
  "min_score": 0.0,
  "page": 1,
  "page_size": 10
}
```

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | `string` | Yes | Search query (1-500 characters) |
| `top_k` | `int` | No | Number of results (default: 10, max: 100) |
| `segment_types` | `string[]` | No | Filter by segment types |
| `meeting_ids` | `string[]` | No | Filter by specific meeting IDs |
| `project_id` | `UUID` | No | Filter by project ID |
| `min_score` | `float` | No | Minimum similarity score (0.0-1.0, default: 0.0) |
| `page` | `int` | No | Page number (default: 1) |
| `page_size` | `int` | No | Results per page (default: 10, max: 100) |

**Response** `200 OK`:
```json
{
  "query": "search query",
  "results": [
    {
      "text": "Matching text content",
      "meeting_id": "meeting_id",
      "segment_type": "transcript",
      "timestamp": 120.5,
      "segment_index": 0,
      "similarity_score": 0.95,
      "distance": 0.05,
      "additional_data": {}
    }
  ],
  "total_results": 25,
  "page": 1,
  "page_size": 10,
  "total_pages": 3,
  "segment_types_filter": ["transcript"],
  "meeting_ids_filter": null
}
```

---

#### `GET /api/v1/search/stats`

Get vector store statistics.

**Response** `200 OK`:
```json
{
  "total_vectors": 1500,
  "projects": {
    "project_uuid_1": 500,
    "project_uuid_2": 1000
  },
  "segment_types": {
    "transcript": 1000,
    "topic": 200,
    "decision": 150,
    "action_item": 100,
    "summary": 50
  }
}
```

---

### Chat

#### `POST /api/v1/chat`

Chat with AI assistant using RAG (Retrieval Augmented Generation).

**Request Body**:
```json
{
  "message": "string (required, 1-2000 chars)",
  "context": "string (optional, max 1000 chars)",
  "project_id": "uuid (optional)"
}
```

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | `string` | Yes | User message (1-2000 characters) |
| `context` | `string` | No | Optional context about current page/view (max 1000 chars) |
| `project_id` | `UUID` | No | Project ID for project-scoped RAG search |

**Response** `200 OK`:
```json
{
  "response": "AI assistant response text...",
  "sources": [
    {
      "meeting_id": "meeting_id",
      "segment_type": "transcript",
      "text": "Relevant text snippet...",
      "similarity": 0.92
    }
  ],
  "used_rag": true
}
```

> **Note**: Performs semantic search on meeting content, then generates LLM response with retrieved context.

---

### Static Files

#### `GET /storage/{path}`

Access stored meeting files (audio, transcripts, etc.).

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `string` | Relative path within storage directory |

**Response** `200 OK`:
- **Content-Type**: Based on file type
- **Body**: File content (binary)

**Example**: `GET /storage/meeting_123/audio/meeting.mp4`

---

## External API Calls

The application makes the following external API calls:

### 1. Mistral AI API

| Property | Value |
|----------|-------|
| **Purpose** | LLM inference for chat, summaries, and agent processing |
| **Endpoint** | `https://api.mistral.ai/v1/chat/completions` (via Mistral SDK) |
| **Authentication** | `MISTRAL_API_KEY` environment variable |
| **Model** | `mistral-small-latest` (default) |
| **Timeout** | 30 seconds |
| **Retry Logic** | Automatic retry with exponential backoff (max 2 retries) |

**Used By**:
- `LLMClient` (chat endpoint, agent processing)
- Summary Agent
- Topic Agent
- Action Item Agent

---

### 2. Groq API

| Property | Value |
|----------|-------|
| **Purpose** | Fast LLM inference for decision extraction |
| **Endpoint** | `https://api.groq.com/openai/v1/chat/completions` |
| **Authentication** | `GROQ_API_KEY` environment variable |
| **Model** | `llama-3.3-70b-versatile` |
| **Timeout** | 60 seconds |
| **Fallback** | Pattern matching if API unavailable |

**Used By**:
- Decision Agent

---

### 3. HuggingFace Inference API

| Property | Value |
|----------|-------|
| **Purpose** | Speaker diarization and sentiment analysis |
| **Endpoint** | `https://api-inference.huggingface.co/models/{model}` |
| **Authentication** | `HUGGINGFACE_TOKEN` environment variable |
| **Timeout** | 30 seconds |
| **Note** | Falls back gracefully if token not provided |

**Used By**:
- Transcription Service (speaker diarization via `pyannote/speaker-diarization-3.1`)
- Sentiment Agent (sentiment analysis models)

---

### 4. WhisperX / OpenAI Whisper

| Property | Value |
|----------|-------|
| **Purpose** | Audio transcription |
| **Type** | Local model (downloaded on first use) |
| **Model** | `small` (default, configurable) |
| **Features** | Word-level timestamps, speaker diarization (via pyannote) |
| **Note** | Runs locally, no external API calls |

**Used By**:
- Transcription Service


---

## Notes

1. **Meeting IDs**: The API supports both UUID format (new) and legacy folder-name format (backward compatibility)

2. **Processing**: File upload triggers automatic background processing pipeline:
   - Transcription → Agent Analysis → Vector Indexing

3. **Storage**: Files are stored in `backend/storage/` directory

4. **Vector Store**: Semantic search uses local vector embeddings (FAISS/ChromaDB)

5. **Database**: PostgreSQL/SQLite database stores projects, meetings, and insights (optional, falls back to filesystem)
