from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


@dataclass
class VectorMetadata:
    """Metadata stored alongside each vector embedding."""
    meeting_id: str
    segment_type: str  # 'transcript', 'topic', 'decision', 'action_item', 'summary'
    text: str
    timestamp: Optional[float] = None
    segment_index: Optional[int] = None
    additional_data: Optional[Dict[str, Any]] = None  # For agent-specific data
    project_id: Optional[str] = None  # Project UUID (optional for backward compatibility)


class VectorStoreService:
    """
    FAISS-based vector store for semantic search across meeting content.
    
    Stores embeddings for:
    - Full meeting transcripts (chunked)
    - Topic segments
    - Decisions
    - Action items
    - Summaries
    """

    def __init__(
        self,
        vector_store_path: Path = Path("storage/vectors"),
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 500,  # Characters per chunk for transcript
        chunk_overlap: int = 50,  # Overlap between chunks
    ):
        """
        Initialize vector store service.
        
        Args:
            vector_store_path: Directory to store FAISS index and metadata
            embedding_model_name: Sentence transformer model name
            chunk_size: Size of text chunks for transcript embedding
            chunk_overlap: Overlap between chunks
        """
        self.vector_store_path = vector_store_path
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        self.embedding_model_name = embedding_model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize embedding model (lazy loading)
        self._embedding_model: Optional[SentenceTransformer] = None
        
        # FAISS index and metadata storage
        self.index: Optional[faiss.Index] = None
        self.metadata_list: List[VectorMetadata] = []
        self.index_path = self.vector_store_path / "faiss.index"
        self.metadata_path = self.vector_store_path / "metadata.json"
        
        # Load existing index if available
        self._load_index()

    @property
    def embedding_model(self) -> SentenceTransformer:
        """Lazy load embedding model."""
        if self._embedding_model is None:
            logger.info(f"[VectorStore] Loading embedding model: {self.embedding_model_name}")
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info("[VectorStore] Embedding model loaded successfully")
        return self._embedding_model

    def _load_index(self) -> None:
        """Load existing FAISS index and metadata from disk."""
        logger.info(f"[VectorStore] Checking for index at: {self.index_path.absolute()}")
        logger.info(f"[VectorStore] Index exists: {self.index_path.exists()}, Metadata exists: {self.metadata_path.exists()}")
        
        if self.index_path.exists() and self.metadata_path.exists():
            try:
                logger.info("[VectorStore] Loading existing FAISS index")
                self.index = faiss.read_index(str(self.index_path))
                
                with self.metadata_path.open("r", encoding="utf-8") as f:
                    metadata_dicts = json.load(f)
                    self.metadata_list = [
                        VectorMetadata(**md) for md in metadata_dicts
                    ]
                
                logger.info(f"[VectorStore] Loaded {len(self.metadata_list)} vectors from disk")
                if self.index is not None:
                    logger.info(f"[VectorStore] FAISS index dimension: {self.index.d}, total vectors: {self.index.ntotal}")
            except Exception as e:
                logger.error(f"[VectorStore] Failed to load existing index: {e}", exc_info=True)
                self.index = None
                self.metadata_list = []
        else:
            logger.info("[VectorStore] No existing index found. Will create new index on first add.")
            self.index = None
            self.metadata_list = []

    def _save_index(self) -> None:
        """Save FAISS index and metadata to disk."""
        if self.index is None or len(self.metadata_list) == 0:
            return
        
        try:
            logger.info(f"[VectorStore] Saving {len(self.metadata_list)} vectors to disk")
            faiss.write_index(self.index, str(self.index_path))
            
            metadata_dicts = [asdict(md) for md in self.metadata_list]
            with self.metadata_path.open("w", encoding="utf-8") as f:
                json.dump(metadata_dicts, f, ensure_ascii=False, indent=2)
            
            logger.info("[VectorStore] Index saved successfully")
        except Exception as e:
            logger.error(f"[VectorStore] Failed to save index: {e}")

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            
            if end >= len(text):
                break
            
            # Move start forward by chunk_size - overlap
            start += self.chunk_size - self.chunk_overlap
        
        return chunks

    def _ensure_index(self, embedding_dim: int) -> None:
        """Ensure FAISS index exists with correct dimension."""
        if self.index is None:
            # Try to load existing index first
            if self.index_path.exists() and self.metadata_path.exists():
                try:
                    logger.info("[VectorStore] Loading existing index before adding vectors")
                    self.index = faiss.read_index(str(self.index_path))
                    # Reload metadata to ensure it's in sync
                    with self.metadata_path.open("r", encoding="utf-8") as f:
                        metadata_dicts = json.load(f)
                        self.metadata_list = [
                            VectorMetadata(**md) for md in metadata_dicts
                        ]
                    logger.info(f"[VectorStore] Loaded existing index with {len(self.metadata_list)} vectors")
                    # Verify dimension matches
                    if self.index.d != embedding_dim:
                        logger.error(f"[VectorStore] Dimension mismatch! Existing: {self.index.d}, New: {embedding_dim}")
                        raise ValueError(f"Embedding dimension mismatch: {self.index.d} != {embedding_dim}")
                except Exception as e:
                    logger.warning(f"[VectorStore] Failed to load existing index: {e}. Creating new index.")
                    self.index = None
                    self.metadata_list = []
            
            # Create new index if still None
            if self.index is None:
                self.index = faiss.IndexFlatL2(embedding_dim)
                logger.info(f"[VectorStore] Created new FAISS index with dimension {embedding_dim}")

    def add_meeting_embeddings(
        self,
        meeting_id: str,
        transcript: Optional[Dict[str, Any]] = None,
        topics: Optional[List[Dict[str, Any]]] = None,
        decisions: Optional[List[Dict[str, Any]]] = None,
        action_items: Optional[List[Dict[str, Any]]] = None,
        summary: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> int:
        """
        Add embeddings for all content from a meeting.
        
        Returns:
            Number of vectors added
        """
        vectors_added = 0
        
        # Add transcript chunks
        if transcript:
            transcript_text = transcript.get("text", "")
            if transcript_text:
                chunks = self._chunk_text(transcript_text)
                segments = transcript.get("segments", [])
                
                for chunk_idx, chunk in enumerate(chunks):
                    # Find corresponding segment for timestamp
                    timestamp = None
                    segment_index = None
                    if segments and chunk_idx < len(segments):
                        seg = segments[chunk_idx]
                        timestamp = seg.get("start")
                        segment_index = chunk_idx
                    
                    metadata = VectorMetadata(
                        meeting_id=meeting_id,
                        segment_type="transcript",
                        text=chunk,
                        timestamp=timestamp,
                        segment_index=segment_index,
                        project_id=project_id,
                    )
                    self._add_vector(metadata)
                    vectors_added += 1
        
        # Add topics
        if topics:
            for topic_idx, topic in enumerate(topics):
                topic_text = topic.get("topic", "") or topic.get("name", "")
                topic_description = topic.get("description", "")
                combined_text = f"{topic_text}. {topic_description}".strip()
                
                if combined_text:
                    metadata = VectorMetadata(
                        meeting_id=meeting_id,
                        segment_type="topic",
                        text=combined_text,
                        timestamp=topic.get("start_time"),
                        segment_index=topic_idx,
                        project_id=project_id,
                        additional_data={
                            "topic": topic_text,
                            "description": topic_description,
                        },
                    )
                    self._add_vector(metadata)
                    vectors_added += 1
        
        # Add decisions
        if decisions:
            for decision_idx, decision in enumerate(decisions):
                decision_text = decision.get("decision", "") or decision.get("text", "")
                context = decision.get("context", "")
                combined_text = f"{decision_text}. {context}".strip()
                
                if combined_text:
                    metadata = VectorMetadata(
                        meeting_id=meeting_id,
                        segment_type="decision",
                        text=combined_text,
                        timestamp=decision.get("timestamp"),
                        segment_index=decision_idx,
                        project_id=project_id,
                        additional_data={
                            "decision": decision_text,
                            "context": context,
                            "participants": decision.get("participants", []),
                            "impact": decision.get("impact"),
                        },
                    )
                    self._add_vector(metadata)
                    vectors_added += 1
        
        # Add action items
        if action_items:
            for action_idx, action in enumerate(action_items):
                action_text = action.get("action", "") or action.get("task", "")
                assignee = action.get("assignee", "")
                deadline = action.get("deadline", "")
                combined_text = f"{action_text}. Assigned to: {assignee}. Deadline: {deadline}".strip()
                
                if combined_text:
                    metadata = VectorMetadata(
                        meeting_id=meeting_id,
                        segment_type="action_item",
                        text=combined_text,
                        timestamp=action.get("timestamp"),
                        segment_index=action_idx,
                        project_id=project_id,
                        additional_data={
                            "action": action_text,
                            "assignee": assignee,
                            "deadline": deadline,
                            "status": action.get("status", "pending"),
                        },
                    )
                    self._add_vector(metadata)
                    vectors_added += 1
        
        # Add summary
        if summary:
            if isinstance(summary, dict):
                summary_text = summary.get("summary", "") or summary.get("text", "")
            else:
                summary_text = str(summary)
            
            if summary_text:
                metadata = VectorMetadata(
                    meeting_id=meeting_id,
                    segment_type="summary",
                    text=summary_text,
                    project_id=project_id,
                    additional_data={"type": "executive_summary"} if isinstance(summary, dict) else None,
                )
                self._add_vector(metadata)
                vectors_added += 1
        
        # Save index after adding vectors
        if vectors_added > 0:
            self._save_index()
            logger.info(f"[VectorStore] Added {vectors_added} vectors for meeting {meeting_id}")
        
        return vectors_added

    def _add_vector(self, metadata: VectorMetadata) -> None:
        """Add a single vector with metadata to the index."""
        # Generate embedding
        embedding = self.embedding_model.encode(metadata.text, convert_to_numpy=True)
        embedding = embedding.astype('float32').reshape(1, -1)
        
        # Ensure index exists with correct dimension
        embedding_dim = embedding.shape[1]
        self._ensure_index(embedding_dim)
        
        # Add to index
        self.index.add(embedding)
        self.metadata_list.append(metadata)

    def search(
        self,
        query: str,
        top_k: int = 10,
        segment_types: Optional[List[str]] = None,
        meeting_ids: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search across stored vectors.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            segment_types: Filter by segment types (e.g., ['decision', 'action_item'])
            meeting_ids: Filter by meeting IDs
            project_id: Filter by project ID (UUID string)
            min_score: Minimum similarity score (0-1, lower is more similar for L2)
        
        Returns:
            List of search results with metadata and scores
        """
        # Try to reload index if it's None (might have been created after initialization)
        if self.index is None:
            logger.info("[VectorStore] Index is None, attempting to reload...")
            self._load_index()
        
        if self.index is None or len(self.metadata_list) == 0:
            logger.warning(f"[VectorStore] No vectors available for search. Index: {self.index is not None}, Metadata count: {len(self.metadata_list)}")
            logger.warning(f"[VectorStore] Index path: {self.index_path.absolute()}, exists: {self.index_path.exists()}")
            logger.warning(f"[VectorStore] Metadata path: {self.metadata_path.absolute()}, exists: {self.metadata_path.exists()}")
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query, convert_to_numpy=True)
        query_embedding = query_embedding.astype('float32').reshape(1, -1)
        
        # Search in FAISS
        k = min(top_k * 2, len(self.metadata_list))  # Get more results for filtering
        distances, indices = self.index.search(query_embedding, k)
        
        # Process results
        results = []
        filtered_count = 0
        for idx, distance in zip(indices[0], distances[0]):
            if idx >= len(self.metadata_list):
                continue
            
            metadata = self.metadata_list[idx]
            
            # Apply filters
            if segment_types and metadata.segment_type not in segment_types:
                filtered_count += 1
                continue
            if meeting_ids and metadata.meeting_id not in meeting_ids:
                filtered_count += 1
                continue
            if project_id is not None:
                # Filter by project_id - only include vectors that match the project_id
                # Vectors with project_id=None (old vectors) are excluded from project-scoped searches
                # Normalize both to strings for comparison
                metadata_pid = str(metadata.project_id) if metadata.project_id is not None else None
                search_pid = str(project_id) if project_id is not None else None
                if metadata_pid != search_pid:
                    filtered_count += 1
                    continue
            
            # Convert L2 distance to similarity score (lower distance = higher similarity)
            # Normalize to 0-1 range (inverse of normalized distance)
            max_distance = max(distances[0]) if len(distances[0]) > 0 else 1.0
            similarity_score = 1.0 - (distance / max_distance) if max_distance > 0 else 1.0
            
            if similarity_score < min_score:
                continue
            
            result = {
                "text": metadata.text,
                "meeting_id": metadata.meeting_id,
                "segment_type": metadata.segment_type,
                "timestamp": metadata.timestamp,
                "segment_index": metadata.segment_index,
                "similarity_score": float(similarity_score),
                "distance": float(distance),
                "additional_data": metadata.additional_data,
            }
            results.append(result)
            
            if len(results) >= top_k:
                break
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        logger.info(
            f"[VectorStore] Search for '{query[:50]}...' returned {len(results)} results "
            f"(filtered out {filtered_count}, project_id={project_id})"
        )
        return results

    def get_meeting_vectors_count(self, meeting_id: str) -> int:
        """Get count of vectors for a specific meeting."""
        return sum(1 for md in self.metadata_list if md.meeting_id == meeting_id)

    def delete_meeting_vectors(self, meeting_id: str) -> bool:
        """
        Delete all vectors for a specific meeting.
        Note: This rebuilds the index, which can be slow for large indices.
        """
        if self.index is None:
            return False
        
        # Filter out vectors for this meeting
        original_count = len(self.metadata_list)
        self.metadata_list = [
            md for md in self.metadata_list if md.meeting_id != meeting_id
        ]
        
        if len(self.metadata_list) == original_count:
            return False  # No vectors to delete
        
        # Rebuild index
        if len(self.metadata_list) == 0:
            self.index = None
        else:
            # Get embedding dimension
            sample_metadata = self.metadata_list[0]
            sample_embedding = self.embedding_model.encode(
                sample_metadata.text, convert_to_numpy=True
            )
            embedding_dim = sample_embedding.shape[0]
            
            # Create new index and add remaining vectors
            self.index = faiss.IndexFlatL2(embedding_dim)
            for metadata in self.metadata_list:
                embedding = self.embedding_model.encode(
                    metadata.text, convert_to_numpy=True
                )
                embedding = embedding.astype('float32').reshape(1, -1)
                self.index.add(embedding)
        
        # Save updated index
        self._save_index()
        logger.info(f"[VectorStore] Deleted vectors for meeting {meeting_id}")
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        if self.index is None:
            return {
                "total_vectors": 0,
                "meetings": {},
                "segment_types": {},
            }
        
        meetings = {}
        segment_types = {}
        projects = {}
        
        for metadata in self.metadata_list:
            # Count by meeting
            meetings[metadata.meeting_id] = meetings.get(metadata.meeting_id, 0) + 1
            
            # Count by segment type
            segment_types[metadata.segment_type] = segment_types.get(metadata.segment_type, 0) + 1
            
            # Count by project
            project_key = metadata.project_id if metadata.project_id else "none"
            projects[project_key] = projects.get(project_key, 0) + 1
        
        return {
            "total_vectors": len(self.metadata_list),
            "embedding_dimension": self.index.d if hasattr(self.index, 'd') else None,
            "meetings": meetings,
            "segment_types": segment_types,
            "projects": projects,
        }
    
    def count_vectors_by_project(self, project_id: str) -> int:
        """Count vectors for a specific project."""
        if project_id is None:
            return 0
        return sum(1 for md in self.metadata_list if md.project_id == project_id)

