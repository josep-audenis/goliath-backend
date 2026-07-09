"""
Agent runtime — OpenAI Agents SDK model factory + JSON helpers.

SDK/LLM are optional. When unavailable, the orchestrator runs a deterministic
pipeline instead (still contract-valid). This module only owns model creation
and result parsing so the orchestrator stays readable.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.config import settings

log = logging.getLogger("app.agent.runtime")

try:
    from agents import Agent, Runner, set_tracing_disabled  # type: ignore
    from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel  # type: ignore
    from openai import AsyncOpenAI  # type: ignore

    set_tracing_disabled(True)
    SDK_AVAILABLE = True
except Exception as e:  # pragma: no cover
    log.warning("openai-agents SDK unavailable: %s", e)
    SDK_AVAILABLE = False


def llm_enabled() -> bool:
    return SDK_AVAILABLE and settings.has_llm_key


def make_model() -> Any:
    if settings.llm_provider == "openai":
        client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        return OpenAIChatCompletionsModel(model=settings.agent_model, openai_client=client)
    if settings.llm_provider == "hf":
        client = AsyncOpenAI(api_key=settings.hf_token, base_url=settings.hf_space_base_url)
        return OpenAIChatCompletionsModel(model=settings.hf_model, openai_client=client)
    client = AsyncOpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url)
    return OpenAIChatCompletionsModel(model=settings.agent_model, openai_client=client)


_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def parse_json(text: str) -> dict[str, Any]:
    if not text:
        return {}
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").lstrip("json").strip()
    try:
        return json.loads(text)
    except Exception:
        m = _JSON_BLOCK.search(text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    log.warning("agent did not return parseable JSON: %r", text[:200])
    return {}


async def run_agent_json(agent: Any, prompt: str, ctx: dict[str, Any] | None = None, max_turns: int = 12) -> dict[str, Any]:
    """Run an SDK Agent and parse its final output as JSON."""
    result = await Runner.run(agent, input=prompt, context=ctx or {}, max_turns=max_turns)
    return parse_json(str(result.final_output))
