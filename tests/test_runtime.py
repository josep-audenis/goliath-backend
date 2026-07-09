"""Runtime helpers — JSON parsing + llm gating (no SDK calls)."""

from __future__ import annotations

from app.agent import runtime


def test_llm_disabled_without_keys():
    # deterministic_mode fixture cleared all provider keys
    assert runtime.llm_enabled() is False


def test_parse_plain_json():
    assert runtime.parse_json('{"a": 1}') == {"a": 1}


def test_parse_fenced_json():
    assert runtime.parse_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_parse_json_embedded_in_prose():
    assert runtime.parse_json('here you go: {"a": 1, "b": [2,3]} thanks') == {"a": 1, "b": [2, 3]}


def test_parse_json_garbage_returns_empty():
    assert runtime.parse_json("not json at all") == {}
    assert runtime.parse_json("") == {}
