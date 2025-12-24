# Meeting Insight Frontend

Minimal React (Vite + TypeScript) UI to interact with the backend.

## Features
- Upload audio/video to `/api/v1/upload`
- Poll processing status `/api/v1/status/{meeting_id}`
- Fetch insights `/api/v1/insights/{meeting_id}`

## Setup
```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

Set API base URL via `.env`:
```
VITE_API_BASE_URL=http://localhost:8000
```

## Expected backend endpoints
- POST `/api/v1/upload` -> `{ meeting_id, status }`
- GET `/api/v1/status/{meeting_id}` -> `{ meeting_id, status }`
- GET `/api/v1/insights/{meeting_id}` -> `{ meeting_id, insights }`

## Notes
- CORS must allow the frontend origin (backend currently wide open; tighten for production).
- Video upload relies on backend ffmpeg support to extract audio.
# Frontend

This directory contains the frontend application for the Meeting Insight Generator.

## Setup

Frontend setup instructions will be added here once the frontend framework is chosen.

## Development

```bash
cd frontend
# Install dependencies and start development server
```

## Tech Stack

To be determined - likely React, Vue, or Next.js.

