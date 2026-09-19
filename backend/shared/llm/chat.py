"""OMNIA LlmChat surface — Gemini via shared.llm (ex-Emergent compatible API)."""

from __future__ import annotations

from typing import Any, AsyncIterator, Optional


class UserMessage:
    def __init__(self, text: str = "", **kwargs: Any):
        self.text = text
        self.kwargs = kwargs


class TextDelta:
    def __init__(self, text: str = "", content: Optional[str] = None, **kwargs: Any):
        # Legacy Emergent used `.content`; stream yields `.text` — expose both.
        payload = content if content is not None else text
        self.text = payload or ""
        self.content = self.text
        self.kwargs = kwargs


def _message_text(message: Any) -> str:
    if message is None:
        return ""
    if isinstance(message, str):
        return message
    return getattr(message, "text", None) or str(message)


class LlmChat:
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
        self.provider = "gemini"
        self.model = None
        self.kwargs = kwargs

    def with_model(self, provider: str, model: str) -> "LlmChat":
        self.provider = provider
        self.model = model
        return self

    async def send_message(self, message: Any = None, **kwargs: Any) -> str:
        from shared.llm import generate_text, resolve_api_key, LlmNotConfigured

        try:
            key = resolve_api_key(self.api_key)
        except LlmNotConfigured as e:
            raise RuntimeError(str(e)) from e
        return await generate_text(
            prompt=_message_text(message),
            system=self.system_message,
            model=self.model,
            api_key=key,
        )

    async def send_message_stream(
        self, message: Any = None, **kwargs: Any
    ) -> AsyncIterator[TextDelta]:
        from shared.llm import generate_text_stream, resolve_api_key, LlmNotConfigured

        try:
            key = resolve_api_key(self.api_key)
        except LlmNotConfigured as e:
            raise RuntimeError(str(e)) from e
        async for chunk in generate_text_stream(
            prompt=_message_text(message),
            system=self.system_message,
            model=self.model,
            api_key=key,
        ):
            yield TextDelta(text=chunk)

    # Alias storico (al_agent / HAL Legal)
    async def stream_message(
        self, message: Any = None, **kwargs: Any
    ) -> AsyncIterator[TextDelta]:
        async for delta in self.send_message_stream(message, **kwargs):
            yield delta
