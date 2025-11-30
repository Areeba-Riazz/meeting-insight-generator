# Meeting Insight Generator
The Meeting Insight Generator is an AI-powered backend system that converts meeting audio into structured, actionable insights. It goes beyond basic transcription by identifying decisions, action items, responsibilities, discussion topics, and sentiments. The system also provides semantic search across past meetings using vector embeddings, enabling teams to quickly recall important discussions and decisions.


## Key Features
- High-accuracy transcription using Whisper
- Topic segmentation
- Decision and responsibility extraction
- Action item and deadline identification
- Sentiment analysis
- Summary generation
- Semantic search across meeting history
- REST API for upload, status, insights, and search
- Modular multi-agent architecture

## Architecture Overview
- Audio Input
- Whisper Transcription
- Multi-Agent Processing
  - Topic Agent
  - Decision Agent
  - Action Item Agent
  - Sentiment Agent
  - Summary Agent
- Vector Store (FAISS)
- Structured JSON Output
