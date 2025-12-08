# Progress Summary

## Completed
- Phase 1: Repo structure (backend/frontend), root venv/deps, Docker configs, env setup, FastAPI skeleton with CORS and health.
- Phase 1.3: Basic API structure in backend (routes/models, health).
- Phase 2.1: Whisper transcription with preprocessing; diarization hook; filesystem transcript store; sample transcription script.
- Phase 2.2: Base agent class; LLM client wired to LangChain Mistral with mock fallback.
- Phase 2.3: Stub agents (topic, decision, action, sentiment, summary).
- Phase 2.4: Orchestrator (parallel with timeouts); API endpoints for upload/status/insights; file-type/size validation; in-memory status/results; filesystem transcripts.

## In Progress / Pending
- Video handling: validate and test mp4/mkv/mov audio extraction; update allowed types post-validation.
- LangChain prompts/tooling: richer prompt templates, tools, better parsing.
- Agent unit tests and end-to-end tests.
- Persistence phase: PostgreSQL models/migrations, swap in-memory stores for DB; FAISS vector store, embedding linkage, and historical search endpoints.
- Frontend: React app (upload → poll status → show insights), env wiring, basic styling, validation, integration test.
- Production hardening: auth, tightened CORS, logging/observability, retries/circuit breakers.

## How to run (current state)
1) `python -m venv venv && source venv/bin/activate` (Windows: `venv\Scripts\activate`)
2) `pip install -r requirements.txt`
3) `cd backend && docker-compose up -d postgres` (DB not yet used; optional for now)
4) Run API: `uvicorn backend.src.main:app --reload`
5) Test upload/status/insights via the exposed endpoints; sample transcription: `python backend/scripts/transcribe_sample.py` with a file at `backend/storage/sample_audio/meeting.mp3`.

## Notes
- Outputs are still stubby for agents (LLM mock fallback when no key/model). Persistence is filesystem/in-memory; DB/FAISS and richer LLM outputs come in next phases.

