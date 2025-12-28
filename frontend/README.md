# Frontend - Meeting Insight Generator

React-based frontend application for the Meeting Insight Generator project. Provides an intuitive interface for uploading meetings, viewing insights, managing projects, and interacting with the AI chatbot.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side navigation
- **Lucide React** - Icon library

## Features

### Pages
- **Projects Page** - View and manage projects, create new projects
- **Project Detail Page** - View meetings within a project, upload new meetings
- **Upload Page** - Upload audio/video files with real-time processing status
- **Insights Page** - View detailed meeting insights (transcript, topics, decisions, action items, sentiment, summary)
- **Search Page** - Semantic search across all meeting content

### Components
- **FloatingChat** - AI assistant with RAG integration for answering questions about meetings
- **InsightsViewer** - Interactive viewer for meeting insights with video synchronization
- **UploadForm** - File upload with drag-and-drop support
- **StatusPoller** - Real-time status updates during processing
- **Toast** - Notification system for user feedback

## Setup

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Configuration

Create `.env.local` file:
```env
VITE_API_BASE_URL=http://localhost:3000
```

### Development

```bash
npm run dev
```

Application runs at `http://localhost:5173`

### Build

```bash
npm run build
```

## API Integration

The frontend communicates with the backend API:

- `POST /api/v1/upload` - Upload meeting files
- `GET /api/v1/status/{meeting_id}` - Get processing status
- `GET /api/v1/insights/{meeting_id}` - Retrieve meeting insights
- `POST /api/v1/search` - Semantic search
- `GET /api/v1/search/stats` - Search statistics
- `POST /api/v1/chat` - Chat with AI assistant
- `GET /api/v1/projects` - List/create projects
- `GET /api/v1/projects/{id}` - Get project details
- `GET /api/v1/projects/{project_id}/meetings` - List project meetings

## Key Features

- **Real-time Status Updates**: Polls backend for processing progress
- **Video Playback**: Synchronized video playback with transcript segments
- **Semantic Search**: Search across transcripts, topics, decisions, and action items
- **AI Chatbot**: Context-aware assistant with RAG for answering questions
- **Project Organization**: Group meetings into projects for better organization
- **Responsive Design**: Modern UI with smooth animations and transitions
