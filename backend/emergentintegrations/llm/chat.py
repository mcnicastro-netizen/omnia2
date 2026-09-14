"""Minimal LlmChat stub — replaced in M1 by shared.llm Gemini adapter."""

from __future__ import annotations

from typing import Any, AsyncIterator, Optional


class UserMessage:
    def __init__(self, text: str = "", **kwargs: Any):
        self.text = text
        self.kwargs = kwargs


class TextDelta:
    def __init__(self, text: str = ""):
        self.text = text


class LlmChat:
    """Drop-in stub matching emergentintegrations.llm.chat.LlmChat surface."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        session_id: Optional[str] = None,
        system_message: Optional[str] = None,
        **kwargs: Any,
    ):
        self.api_key = api_key
        self.session_id = session_id
        self.system_message = system_message
        self.provider = None
        self.model = None
        self.kwargs = kwargs

    def with_model(self, provider: str, model: str) -> "LlmChat":
        self.provider = provider
        self.model = model
        return self

    async def send_message(self, message: Any = None, **kwargs: Any) -> str:
        raise RuntimeError(
            "LLM bridge not configured. Complete M1: set GEMINI_API_KEY "
            "and migrate to shared.llm (Emergent LlmChat removed)."
        )

    async def send_message_stream(
        self, message: Any = None, **kwargs: Any
    ) -> AsyncIterator[TextDelta]:
        raise RuntimeError(
            "LLM bridge not configured. Complete M1: set GEMINI_API_KEY "
            "and migrate to shared.llm (Emergent LlmChat removed)."
        )
        yield TextDelta("")  # pragma: no cover — makes this an async generator
