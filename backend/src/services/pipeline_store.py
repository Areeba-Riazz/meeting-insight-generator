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

    def set_status(self, meeting_id: str, status: str) -> None:
        self._status[meeting_id] = status
        print(f"[PipelineStore] Meeting {meeting_id[:8]}... status set to: {status}")  # Debug logging

    def get_status(self, meeting_id: str) -> Optional[str]:
        return self._status.get(meeting_id)

    def set_result(self, meeting_id: str, result: Dict[str, Any]) -> None:
        self._results[meeting_id] = result

    def get_result(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        return self._results.get(meeting_id)

