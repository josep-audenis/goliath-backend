"""
Credible mock research output.

Subagents may be mocked for the demo (see roadmap.md). The rule: mock output
must be shape-identical to real output so the frontend never blocks on live
data. These builders produce deterministic-but-plausible companies/opportunities
derived from the query so different queries look different.
"""

from __future__ import annotations

import hashlib
from typing import Any

_SECTORS = ["AI infrastructure", "fintech", "climate tech", "healthtech", "developer tools", "robotics"]
_STAGES = ["pre-seed", "seed", "Series A", "Series B"]
_STATUS_CYCLE = ["hot", "warming", "neutral", "cooling", "not_hot"]
_RISK_CYCLE = ["low", "medium", "high"]


def _seed(query: str, salt: str = "") -> int:
    return int(hashlib.sha256((query + salt).encode()).hexdigest(), 16)


def mock_companies(query: str, geo: str | None, sector: str | None, n: int = 5) -> list[dict[str, Any]]:
    base = _seed(query)
    out: list[dict[str, Any]] = []
    for i in range(n):
        h = _seed(query, str(i))
        score = 55 + (h % 41)  # 55..95
        out.append(
            {
                "name": f"{_pick(_ADJ, h)} {_pick(_NOUN, h >> 8)}",
                "sector": sector or _SECTORS[(base + i) % len(_SECTORS)],
                "geo": geo or "Barcelona",
                "stage": _STAGES[(h >> 4) % len(_STAGES)],
                "goliathScore": float(score),
                "status": _STATUS_CYCLE[(h >> 6) % len(_STATUS_CYCLE)],
                "confidence": float(50 + (h % 46)),
                "riskLevel": _RISK_CYCLE[(h >> 10) % len(_RISK_CYCLE)],
            }
        )
    return sorted(out, key=lambda c: c["goliathScore"], reverse=True)


_ADJ = ["Nova", "Lumen", "Vela", "Orbit", "Quanta", "Aster", "Fathom", "Cobalt", "Ember", "Vertex"]
_NOUN = ["Labs", "AI", "Systems", "Dynamics", "Compute", "Health", "Grid", "Robotics", "Capital", "Works"]


def _pick(arr: list[str], h: int) -> str:
    return arr[h % len(arr)]


def mock_evidence(topic: str) -> list[dict[str, str]]:
    return [
        {"source": "news", "title": f"{topic}: funding momentum accelerates", "url": "https://example.com/news/1"},
        {"source": "web", "title": f"Market map — {topic}", "url": "https://example.com/market/2"},
    ]
