"""Audio serving — backend proxies ElevenLabs output; keys never reach the browser."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.store.audio_store import audio_store

router = APIRouter(prefix="/api/audio", tags=["audio"])


@router.get("/{audio_id}")
async def get_audio(audio_id: str) -> Response:
    item = audio_store.get(audio_id)
    if item is None:
        raise HTTPException(status_code=404, detail="audio not found")
    audio, mime = item
    return Response(content=audio, media_type=mime, headers={"Cache-Control": "public, max-age=3600"})
