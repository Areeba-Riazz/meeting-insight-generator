from __future__ import annotations

import threading
from typing import Any, Dict, Optional


class PipelineStore:
    """
    Simple in-memory store for pipeline results and statuses.
    Persistence is deferred to the FAISS/DB phase.
    """

    def __init__(self) -> None:
        self._status: Dict[str, str] = {}
        self._results: Dict[str, Dict[str, Any]] = {}
        self._progress: Dict[str, float] = {}  # Progress percentage (0-100)
        self._stage: Dict[str, str] = {}  # Human-readable stage description
        self._processing_lock = threading.Lock()
        self._is_processing = False

    def acquire_processing(self) -> bool:
        """Try to acquire processing lock. Returns True if acquired, False if already processing."""
        with self._processing_lock:
            if self._is_processing:
                return False
            self._is_processing = True
            return True

    def release_processing(self) -> None:
        """Release processing lock."""
        with self._processing_lock:
            self._is_processing = False

    def is_processing(self) -> bool:
        """Check if currently processing."""
        with self._processing_lock:
            return self._is_processing

    def set_status(
        self, 
        meeting_id: str, 
        status: str, 
        progress: Optional[float] = None,
        stage: Optional[str] = None
    ) -> None:
        self._status[meeting_id] = status
        if progress is not None:
            self._progress[meeting_id] = progress
        if stage is not None:
            self._stage[meeting_id] = stage
        print(f"[PipelineStore] Meeting {meeting_id[:8]}... status: {status}, progress: {progress}%, stage: {stage}")

    def get_status(self, meeting_id: str) -> Optional[str]:
        return self._status.get(meeting_id)

    def get_progress(self, meeting_id: str) -> Optional[float]:
        return self._progress.get(meeting_id)

    def get_stage(self, meeting_id: str) -> Optional[str]:
        return self._stage.get(meeting_id)

    def set_result(self, meeting_id: str, result: Dict[str, Any]) -> None:
        self._results[meeting_id] = result

    def get_result(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        return self._results.get(meeting_id)

