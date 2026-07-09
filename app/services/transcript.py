"""Transcript helpers for subtitle-style playback.

Current timing is estimated from text because TTS alignment is not stored yet.
Shape is explicit so exact provider timing can replace this later without
changing the endpoint contract.
"""

from __future__ import annotations

import re

from app.schemas.contract import Report, ReportTranscript, TranscriptSegment, TranscriptWord

WORDS_PER_MINUTE = 155
MIN_SEGMENT_MS = 1200
WORD_RE = re.compile(r"\S+")


def estimate_words(script: str) -> tuple[list[TranscriptWord], int]:
    raw_words = [m.group(0) for m in WORD_RE.finditer(script)]
    if not raw_words:
        return [], 0

    duration_ms = max(MIN_SEGMENT_MS, round(len(raw_words) / WORDS_PER_MINUTE * 60_000))
    base = duration_ms / len(raw_words)

    words: list[TranscriptWord] = []
    for idx, word in enumerate(raw_words):
        start_ms = round(idx * base)
        end_ms = duration_ms if idx == len(raw_words) - 1 else round((idx + 1) * base)
        words.append(TranscriptWord(text=word, startMs=start_ms, endMs=end_ms))
    return words, duration_ms


def build_report_transcript(report: Report) -> ReportTranscript:
    segments: list[TranscriptSegment] = []
    for segment in report.segments:
        words, duration_ms = estimate_words(segment.script)
        segments.append(
            TranscriptSegment(
                agentId=segment.agentId,
                script=segment.script,
                subtitle=segment.subtitle,
                audioUrl=segment.audioUrl,
                durationMs=duration_ms,
                words=words,
            )
        )
    return ReportTranscript(runId=report.runId, query=report.query, segments=segments)
