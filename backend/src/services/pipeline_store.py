from __future__ import annotations

from typing import Any, Dict, Optional


class PipelineStore:
    """
    Simple in-memory store for pipeline results and statuses.
    Persistence is deferred to the FAISS/DB phase.
    """

    def __init__(self) -> None:
        self._status: Dict[str, str] = {}
        self._results: Dict[str, Dict[str, Any]] = {}

    def set_status(self, meeting_id: str, status: str) -> None:
        self._status[meeting_id] = status

    def get_status(self, meeting_id: str) -> Optional[str]:
        return self._status.get(meeting_id)

    def set_result(self, meeting_id: str, result: Dict[str, Any]) -> None:
        self._results[meeting_id] = result

    def get_result(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        return self._results.get(meeting_id)

