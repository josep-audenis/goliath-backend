"""
In-memory audio store — holds synthesized segment audio for serving.

Same swappable-storage stance as run_store: hackathon-simple, process-local.
Swap for disk / object storage later without touching callers.
"""

from __future__ import annotations

import threading
import uuid

_MIME = {"mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg"}


class AudioStore:
    def __init__(self) -> None:
        self._data: dict[str, tuple[bytes, str]] = {}
        self._timings: dict[str, list[dict]] = {}
        self._lock = threading.RLock()

    def put(self, audio: bytes, ext: str = "mp3", word_timings: list[dict] | None = None) -> str:
        audio_id = uuid.uuid4().hex[:16]
        with self._lock:
            self._data[audio_id] = (audio, _MIME.get(ext, "application/octet-stream"))
            if word_timings:
                self._timings[audio_id] = word_timings
        return audio_id

    def get(self, audio_id: str) -> tuple[bytes, str] | None:
        with self._lock:
            return self._data.get(audio_id)

    def get_timings(self, audio_id: str) -> list[dict] | None:
        """Provider word timings for this audio, or None if only estimated timing exists."""
        with self._lock:
            return self._timings.get(audio_id)


audio_store = AudioStore()
