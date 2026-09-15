"""OMNIA shared LLM client — Gemini (replaces Emergent LlmChat).

Key resolution order:
  GEMINI_API_KEY → GOOGLE_API_KEY → EMERGENT_LLM_KEY (legacy env name only)

Default model: gemini-2.0-flash (override via GEMINI_MODEL).
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, AsyncIterator, Optional

logger = logging.getLogger("omnia.llm")

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

# Tried in order on 404/503 (high demand / retired model ids).
_MODEL_FALLBACKS = (
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
)

# Brief pause before trying the next model on transient overload.
_RETRY_PAUSE_SEC = 0.9


class LlmNotConfigured(RuntimeError):
    pass


class LlmBusy(RuntimeError):
    """All models exhausted due to transient overload (503 / high demand)."""


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
    aliases = {
        "gemini-3.6-flash": "gemini-3.5-flash",
        "gemini-3.7-flash": "gemini-3.5-flash",
        "gemini-3.8-flash": "gemini-3.5-flash",
        "gemini-3-flash-preview": "gemini-3.5-flash",
        "gemini-3-flash": "gemini-3.5-flash",
        "gemini-2.5-flash": "gemini-3.5-flash",
        "gemini-2.0-flash": "gemini-3.5-flash",
        "gemini-2.0-flash-001": "gemini-3.5-flash",
        "gemini-1.5-flash": "gemini-3.5-flash",
        "gemini-2.5-flash-lite": "gemini-3.5-flash-lite",
        "gemini-2.0-flash-lite": "gemini-3.5-flash-lite",
    }
    return aliases.get(name, name)


def _model_candidates(preferred: Optional[str] = None) -> list[str]:
    first = _normalize_model(None, preferred)
    out: list[str] = []
    for m in (first, *_MODEL_FALLBACKS):
        if m and m not in out:
            out.append(m)
    return out


def _is_retryable_model_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code in (404, 429, 503):
        return True
    return any(
        s in msg
        for s in (
            "404",
            "503",
            "429",
            "not_found",
            "unavailable",
            "high demand",
            "no longer available",
            "is not found",
            "resource_exhausted",
        )
    )


def _is_busy_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code in (429, 503):
        return True
    return any(
        s in msg
        for s in ("503", "429", "high demand", "unavailable", "resource_exhausted")
    )


def _extract_text(resp: Any) -> str:
    text = getattr(resp, "text", None) or ""
    if not text and getattr(resp, "candidates", None):
        try:
            text = resp.candidates[0].content.parts[0].text
        except Exception:
            text = str(resp)
    return (text or "").strip()


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
    client = genai.Client(api_key=key)
    contents = prompt
    config: dict[str, Any] = {"temperature": temperature}
    if system:
        config["system_instruction"] = system

    last_err: Optional[BaseException] = None
    candidates = _model_candidates(model)
    for i, model_id in enumerate(candidates):
        try:
            try:
                resp = await client.aio.models.generate_content(
                    model=model_id,
                    contents=contents,
                    config=config,
                )
            except Exception as aio_err:
                if _is_retryable_model_error(aio_err):
                    raise aio_err
                logger.warning(
                    "aio generate_content failed on %s (%s); trying sync",
                    model_id,
                    aio_err,
                )
                resp = client.models.generate_content(
                    model=model_id,
                    contents=contents,
                    config=config,
                )
            return _extract_text(resp)
        except Exception as e:
            last_err = e
            if _is_retryable_model_error(e):
                logger.warning(
                    "LLM model %s unavailable (%s); trying fallback", model_id, e
                )
                if _is_busy_error(e) and i < len(candidates) - 1:
                    await asyncio.sleep(_RETRY_PAUSE_SEC)
                continue
            raise
    assert last_err is not None
    if _is_busy_error(last_err):
        raise LlmBusy(str(last_err)) from last_err
    raise last_err


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
    client = genai.Client(api_key=key)
    config: dict[str, Any] = {"temperature": temperature}
    if system:
        config["system_instruction"] = system

    last_err: Optional[BaseException] = None
    candidates = _model_candidates(model)
    for i, model_id in enumerate(candidates):
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
            return
        except Exception as e:
            last_err = e
            if _is_retryable_model_error(e):
                logger.warning(
                    "LLM stream model %s unavailable (%s); trying fallback",
                    model_id,
                    e,
                )
                if _is_busy_error(e) and i < len(candidates) - 1:
                    await asyncio.sleep(_RETRY_PAUSE_SEC)
                continue
            break

    logger.warning("stream unavailable (%s); falling back to single response", last_err)
    try:
        text = await generate_text(
            prompt=prompt,
            system=system,
            model=model,
            api_key=api_key,
            temperature=temperature,
        )
    except LlmBusy:
        raise
    except Exception:
        if last_err and _is_busy_error(last_err):
            raise LlmBusy(str(last_err)) from last_err
        raise
    if text:
        yield text
