from __future__ import annotations

from typing import Any

# DeepSeek disk cache is on by default — no cache_control flags.
# Hits require an identical prefix across requests. Keep these stable:
#   1. SYSTEM_PROMPT — never interpolate session ids, timestamps, or user names
#   2. Tool names/descriptions/order — byte-stable in tools.py
#   3. History — append-only; don't reorder or rewrite prior turns


def extract_turn_usage(output: Any) -> dict[str, int]:
    """Read DeepSeek cache stats from a LangChain model response."""
    turn = {"input": 0, "output": 0, "cacheRead": 0, "cacheMiss": 0}

    usage_meta = getattr(output, "usage_metadata", None)
    if usage_meta:
        turn["input"] = int(getattr(usage_meta, "input_tokens", 0) or 0)
        turn["output"] = int(getattr(usage_meta, "output_tokens", 0) or 0)

    resp = getattr(output, "response_metadata", None) or {}
    token_usage = resp.get("token_usage") or resp.get("usage") or {}

    # DeepSeek-specific fields (also surfaced via OpenAI-compatible usage block)
    hit = token_usage.get("prompt_cache_hit_tokens")
    miss = token_usage.get("prompt_cache_miss_tokens")
    if hit is not None:
        turn["cacheRead"] = int(hit)
    if miss is not None:
        turn["cacheMiss"] = int(miss)

    return turn


def merge_usage(total: dict[str, int], turn: dict[str, int]) -> dict[str, int]:
    return {
        "input": total.get("input", 0) + turn.get("input", 0),
        "output": total.get("output", 0) + turn.get("output", 0),
        "cacheRead": total.get("cacheRead", 0) + turn.get("cacheRead", 0),
        "cacheMiss": total.get("cacheMiss", 0) + turn.get("cacheMiss", 0),
    }
