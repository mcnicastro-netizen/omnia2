"""OMNIA shared LLM client — Gemini (replaces Emergent LlmChat).

Key resolution order:
  GEMINI_API_KEY → GOOGLE_API_KEY → EMERGENT_LLM_KEY (legacy env name only)

Default model: gemini-2.0-flash (override via GEMINI_MODEL).
"""
from __future__ import annotations

import logging
import os
from typing import Any, AsyncIterator, Optional

logger = logging.getLogger("omnia.llm")

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")


class LlmNotConfigured(RuntimeError):
    pass


def resolve_api_key(explicit: Optional[str] = None) -> str:
    key = (
        explicit
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("EMERGENT_LLM_KEY")
        or ""
    ).strip()
    if not key:
        raise LlmNotConfigured(
            "No LLM API key. Set GEMINI_API_KEY (preferred) in backend/.env"
        )
    return key


def _normalize_model(provider: Optional[str], model: Optional[str]) -> str:
    """Map legacy Emergent model names to Google API model ids."""
    name = (model or DEFAULT_MODEL).strip()
    # Emergent used gemini-3-flash-preview — map to a current Flash id
    aliases = {
        "gemini-3-flash-preview": DEFAULT_MODEL,
        "gemini-3-flash": DEFAULT_MODEL,
        "gemini-1.5-flash": "gemini-1.5-flash",
        "gemini-2.0-flash": "gemini-2.0-flash",
    }
    return aliases.get(name, name)


async def generate_text(
    *,
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.4,
) -> str:
    from google import genai

    key = resolve_api_key(api_key)
    model_id = _normalize_model(None, model)
    client = genai.Client(api_key=key)
    contents = prompt
    config: dict[str, Any] = {"temperature": temperature}
    if system:
        config["system_instruction"] = system
    try:
        resp = await client.aio.models.generate_content(
            model=model_id,
            contents=contents,
            config=config,
        )
    except Exception:
        # Fallback sync if aio path fails on older builds
        logger.exception("aio generate_content failed; trying sync")
        resp = client.models.generate_content(
            model=model_id,
            contents=contents,
            config=config,
        )
    text = getattr(resp, "text", None) or ""
    if not text and getattr(resp, "candidates", None):
        try:
            text = resp.candidates[0].content.parts[0].text
        except Exception:
            text = str(resp)
    return (text or "").strip()


async def generate_text_stream(
    *,
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.4,
) -> AsyncIterator[str]:
    from google import genai

    key = resolve_api_key(api_key)
    model_id = _normalize_model(None, model)
    client = genai.Client(api_key=key)
    config: dict[str, Any] = {"temperature": temperature}
    if system:
        config["system_instruction"] = system
    try:
        stream = await client.aio.models.generate_content_stream(
            model=model_id,
            contents=prompt,
            config=config,
        )
        async for chunk in stream:
            t = getattr(chunk, "text", None)
            if t:
                yield t
    except Exception:
        # Fallback: single-shot then yield once
        logger.warning("stream unavailable; falling back to single response")
        text = await generate_text(
            prompt=prompt, system=system, model=model, api_key=api_key, temperature=temperature
        )
        if text:
            yield text
