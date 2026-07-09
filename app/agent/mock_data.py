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


def _seed(query: str, salt: str = "") -> int:
    return int(hashlib.sha256((query + salt).encode()).hexdigest(), 16)


def _unit(query: str, salt: str) -> float:
    """Deterministic 0-1 value from query+salt (for a sub-signal)."""
    return (_seed(query, salt) % 1000) / 1000.0


def market_heat(query: str, sector: str) -> float:
    """Sector/geo demand momentum — shared by every company in a sector."""
    return _unit(sector, f"heat|{query}")


def mock_companies(query: str, geo: str | None, sector: str | None, n: int = 5) -> list[dict[str, Any]]:
    base = _seed(query)
    out: list[dict[str, Any]] = []
    for i in range(n):
        h = _seed(query, str(i))
        sec = sector or _SECTORS[(base + i) % len(_SECTORS)]
        out.append(
            {
                "name": f"{_pick(_ADJ, h)} {_pick(_NOUN, h >> 8)}",
                "sector": sec,
                "geo": geo or "Barcelona",
                "stage": _STAGES[(h >> 4) % len(_STAGES)],
                # Four 0-1 sub-signals, one per research agent. The scoring engine
                # (app/agent/scoring.py) turns these into goliathScore + breakdown.
                "signals": {
                    "traction": _unit(query, f"traction|{i}"),
                    "funding_timing": _unit(query, f"funding|{i}"),
                    "market_heat": market_heat(query, sec),  # shared per sector
                    "risk": _unit(query, f"risk|{i}"),
                },
                "coverage": 1.0,  # all signals are real in the mock path
            }
        )
    return out


_ADJ = ["Nova", "Lumen", "Vela", "Orbit", "Quanta", "Aster", "Fathom", "Cobalt", "Ember", "Vertex"]
_NOUN = ["Labs", "AI", "Systems", "Dynamics", "Compute", "Health", "Grid", "Robotics", "Capital", "Works"]


def _pick(arr: list[str], h: int) -> str:
    return arr[h % len(arr)]


def mock_evidence(topic: str) -> list[dict[str, str]]:
    return [
        {"source": "news", "title": f"{topic}: funding momentum accelerates", "url": "https://example.com/news/1"},
        {"source": "web", "title": f"Market map — {topic}", "url": "https://example.com/market/2"},
    ]
