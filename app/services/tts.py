"""
ElevenLabs text-to-speech — backend-side only (keys never reach the frontend).

Contract: each PresentationSegment MAY carry an audioUrl; a missing audioUrl is
valid and the frontend falls back to subtitle text. So this is best-effort: with
no key it is a clean no-op, and it never raises into the orchestrator.

Extension point: when wired, synthesize per-segment audio with the owning
agent's voice, store the bytes (disk / object store), and set `segment.audioUrl`
to a backend-served URL.
"""

from __future__ import annotations

import logging
from typing import Sequence

from app.core.config import settings
from app.schemas.contract import AgentPlan, PresentationSegment

log = logging.getLogger("app.services.tts")


def enabled() -> bool:
    return bool(settings.elevenlabs_api_key)


async def attach_audio(segments: Sequence[PresentationSegment], agents: Sequence[AgentPlan]) -> None:
    """Populate segment.audioUrl in place. No-op (leaves None) when disabled."""
    if not enabled():
        return
    voice_by_agent = {a.id: a.voice for a in agents}
    for seg in segments:
        try:
            # TODO: synthesize seg.script with voice_by_agent[seg.agentId], store,
            # then set seg.audioUrl to the served URL. Left unset for now so the
            # frontend uses subtitles.
            _ = voice_by_agent.get(seg.agentId)
        except Exception:
            log.exception("tts failed for segment %s — leaving audioUrl unset", seg.agentId)
