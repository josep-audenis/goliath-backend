"""
ElevenLabs client — text-to-speech (and speech-to-text).

Backend-side only; the key never reaches the frontend (hard constraint, see
external-services.md). Returns raw audio bytes; storing/serving is the caller's
job (see app/store/audio_store.py + app/api/routes/audio.py).
"""

from __future__ import annotations

import logging
import re
import zlib
from typing import Optional

import httpx

from app.core.config import settings

log = logging.getLogger("app.clients.elevenlabs")

# ElevenLabs voice_ids are 20-char alphanumeric. Anything else is a label.
_VOICE_ID_RE = re.compile(r"^[A-Za-z0-9]{20}$")

# Stable ElevenLabs default-voice IDs, mapped to the roster's voice labels.
VOICE_IDS: dict[str, str] = {
    "Aria": "9BWtsMINqrJLrRacOk9x",
    "Roger": "CwhRBWXzGAHq8TQ4Fs17",
    "Sarah": "EXAVITQu4vr4xnSDxMaL",
    "Charlie": "IKne3meq5aSn9XLyUdCD",
    "George": "JBFqnCBsd6RMkjVDRZzb",
}
DEFAULT_VOICE_ID = VOICE_IDS["Aria"]

TTS_MODEL = "eleven_multilingual_v2"
STT_MODEL = "scribe_v1"


class ElevenLabsError(RuntimeError):
    pass


def enabled() -> bool:
    return bool(settings.elevenlabs_api_key)


_VOICE_POOL = list(VOICE_IDS.values())


def resolve_voice(voice: Optional[str]) -> str:
    """
    Always return a REAL ElevenLabs voice_id.

    - known roster label ('Aria') -> its id
    - a real 20-char voice_id      -> passed through
    - anything else (e.g. an LLM-invented label like 'Hunter') -> deterministic
      pick from the pool so each distinct label still gets a distinct, valid
      voice instead of 404ing.
    """
    if not voice:
        return DEFAULT_VOICE_ID
    if voice in VOICE_IDS:
        return VOICE_IDS[voice]
    if _VOICE_ID_RE.match(voice):
        return voice
    return _VOICE_POOL[zlib.crc32(voice.encode()) % len(_VOICE_POOL)]


def text_to_speech(text: str, voice: Optional[str] = None, output_format: str = "mp3_44100_128") -> bytes:
    """Synthesize speech. Returns mp3 bytes. Raises ElevenLabsError on failure."""
    if not enabled():
        raise ElevenLabsError("no ELEVENLABS_API_KEY configured")
    voice_id = resolve_voice(voice)
    url = f"{settings.elevenlabs_base_url}/text-to-speech/{voice_id}"
    try:
        with httpx.Client(timeout=120.0) as c:
            r = c.post(
                url,
                headers={"xi-api-key": settings.elevenlabs_api_key, "Content-Type": "application/json"},
                params={"output_format": output_format},
                json={"text": text, "model_id": TTS_MODEL},
            )
            r.raise_for_status()
            return r.content
    except httpx.HTTPError as e:
        raise ElevenLabsError(f"{type(e).__name__}: {e}") from e


def speech_to_text(audio: bytes, filename: str = "audio.mp3") -> str:
    """Transcribe audio bytes to text (e.g. a spoken VC query). Returns the transcript."""
    if not enabled():
        raise ElevenLabsError("no ELEVENLABS_API_KEY configured")
    url = f"{settings.elevenlabs_base_url}/speech-to-text"
    try:
        with httpx.Client(timeout=120.0) as c:
            r = c.post(
                url,
                headers={"xi-api-key": settings.elevenlabs_api_key},
                data={"model_id": STT_MODEL},
                files={"file": (filename, audio, "application/octet-stream")},
            )
            r.raise_for_status()
            return r.json().get("text", "")
    except httpx.HTTPError as e:
        raise ElevenLabsError(f"{type(e).__name__}: {e}") from e
