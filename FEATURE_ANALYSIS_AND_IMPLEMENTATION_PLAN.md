# Feature Analysis & Implementation Plan

## Current State Analysis

### 1. UI Modernization
**Current State:**
- Basic React UI with functional components
- Inline styles throughout components
- Basic color scheme and layout
- No design system or component library
- Search page exists separately from project context

**Improvements Needed:**
- Modern design system (consider Tailwind CSS or styled-components)
- Consistent color palette and typography
- Better spacing, shadows, and animations
- Improved card layouts and visual hierarchy
- Enhanced search UI integrated within project context
- Responsive design improvements
- Loading states and skeleton screens
- Better error states and empty states

### 2. Project-Scoped RAG Search
**Current State:**
- Database has `Project` and `Meeting` models with `project_id` foreign key
- Vector store stores embeddings with `meeting_id` in metadata but no `project_id`
- Search endpoint exists but searches globally across all meetings
- SearchPage is separate from project context
- No project-scoped search integration

**Gap:**
- Vector store metadata missing `project_id` linkage
- Search API doesn't support project-scoped filtering
- Upload route doesn't associate project_id with embeddings
- Frontend search is global, not project-contextual

**Solution Approach:**
- Add `project_id` to `VectorMetadata` dataclass
- Update `add_meeting_embeddings` to include project_id from meeting metadata/database
- Modify search endpoint to accept `project_id` parameter and automatically filter to that project's meetings
- Integrate search UI directly into `ProjectDetailPage` (not separate page)
- Remove or repurpose global SearchPage
- Search bar appears within project context, automatically scoped to current project

### 3. Enhanced Chatbot with RAG Integration
**Current State:**
- `FloatingChat` component exists in frontend
- Chat API endpoint uses LLM directly without RAG
- No integration with vector store for context retrieval
- Chat responses are generic, not meeting-aware

**Enhancement Needed:**
- Integrate RAG pipeline: user query → vector search (project-scoped) → retrieve relevant meeting context → LLM with context
- Chat automatically filters by current project context
- Show source citations (which meetings/segments informed the response)
- Maintain conversation history for better context
- Add option to toggle between "raw RAG results" and "enhanced LLM response"
- Update chat UI to display sources and allow switching modes

## Implementation Priority

1. **Project-Scoped RAG** (Foundation - enables project-aware search and chat)
2. **Enhanced Chatbot with RAG** (Builds on project filtering)
3. **UI Modernization** (Can be done incrementally)

## Key Files to Modify

### Backend
- `backend/src/services/vector_store_service.py` - Add project_id to VectorMetadata and search logic
- `backend/src/api/routes/search.py` - Add project_id parameter, convert to meeting_ids filter
- `backend/src/api/routes/upload.py` - Include project_id when creating embeddings
- `backend/src/api/routes/chat.py` - Integrate RAG pipeline with project_id filtering
- `backend/src/api/models/request.py` - Add project_id to search/chat requests
- `backend/src/api/models/response.py` - Add project context to responses

### Frontend
- `frontend/src/pages/ProjectDetailPage.tsx` - Integrate search UI component
- `frontend/src/components/FloatingChat.tsx` - Add RAG mode toggle, source display, project context
- `frontend/src/api/client.ts` - Update search/chat API calls to include project_id
- `frontend/src/types/api.ts` - Add project_id types
- `frontend/src/pages/SearchPage.tsx` - Remove or repurpose (search now project-scoped)
- All UI components - Modernize styling and layout

## Technical Considerations

- **Backward Compatibility:** Existing vectors won't have project_id - need migration strategy or default handling
- **Performance:** RAG + LLM adds latency - consider caching and async processing
- **Cost:** LLM API calls increase with RAG integration - monitor usage
- **User Experience:** Show loading states during RAG retrieval and LLM generation
- **Data Consistency:** Ensure project_id is always available when meetings are created and indexed
- **Project Context:** Search and chat must receive project_id from route params or component state
