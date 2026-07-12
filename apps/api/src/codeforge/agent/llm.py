from __future__ import annotations

from langchain_deepseek import ChatDeepSeek

from codeforge.config import settings


def create_llm() -> ChatDeepSeek:
    """Single factory — stable config helps DeepSeek prefix cache hits."""
    return ChatDeepSeek(
        api_key=settings.deepseek_api_key,
        model=settings.model,
        temperature=0,
        max_tokens=8192,
        max_retries=2,
    )
