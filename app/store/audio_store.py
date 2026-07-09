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
        self._lock = threading.RLock()

    def put(self, audio: bytes, ext: str = "mp3") -> str:
        audio_id = uuid.uuid4().hex[:16]
        with self._lock:
            self._data[audio_id] = (audio, _MIME.get(ext, "application/octet-stream"))
        return audio_id

    def get(self, audio_id: str) -> tuple[bytes, str] | None:
        with self._lock:
            return self._data.get(audio_id)


audio_store = AudioStore()
