"""
Presentation TTS — synth each segment with its agent's voice, store the audio,
set segment.audioUrl.

Backend-side only (keys never reach the frontend). Best-effort: any failure
leaves audioUrl unset and the frontend falls back to subtitle text — a run never
breaks because of audio. Synthesis runs concurrently across segments since
ElevenLabs latency dominates.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Sequence

from app.clients import elevenlabs
from app.schemas.contract import AgentPlan, PresentationSegment
from app.store.audio_store import audio_store

log = logging.getLogger("app.services.tts")


def enabled() -> bool:
    return elevenlabs.enabled()


def _assign_distinct_voices(agents: Sequence[AgentPlan]) -> dict[str, str]:
    """
    Map agentId -> a REAL voice_id, distinct per agent where the pool allows.

    Each agent's own voice (roster label or real id) is preferred; on collision
    the next free pool voice is used so orbs sound distinct. Beyond the pool size
    voices necessarily repeat.
    """
    pool = elevenlabs._VOICE_POOL
    used: set[str] = set()
    out: dict[str, str] = {}
    for a in agents:
        vid = elevenlabs.resolve_voice(a.voice)
        if vid in used:
            free = next((v for v in pool if v not in used), vid)
            vid = free
        used.add(vid)
        out[a.id] = vid
    return out


async def attach_audio(segments: Sequence[PresentationSegment], agents: Sequence[AgentPlan]) -> None:
    """Populate segment.audioUrl in place. No-op (leaves None) when disabled."""
    if not enabled() or not segments:
        return
    voice_by_agent = _assign_distinct_voices(agents)

    async def _one(seg: PresentationSegment) -> None:
        try:
            voice_id = voice_by_agent.get(seg.agentId) or elevenlabs.DEFAULT_VOICE_ID
            # Timed synth gives real clip-relative word alignment for karaoke subtitles.
            audio, word_timings = await asyncio.to_thread(elevenlabs.text_to_speech_timed, seg.script, voice_id)
            audio_id = audio_store.put(audio, ext="mp3", word_timings=word_timings)
            seg.audioUrl = f"/api/audio/{audio_id}"
        except Exception:
            log.exception("tts failed for segment %s — leaving audioUrl unset", seg.agentId)

    await asyncio.gather(*(_one(s) for s in segments))
